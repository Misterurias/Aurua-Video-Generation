"""Deterministic Renderer (not an agent).

Takes generated Manim scene code and compiles it into video files using
the manim CLI. Optionally muxes audio in via ffmpeg.

This module is deliberately simple: subprocess calls, no LLM, no retries
beyond what manim itself provides. If a scene fails to render, we log the
error and skip it rather than failing the whole run.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

from ..state import RunState, RunStatus
from .. import config


def render_all_scenes(state: RunState, quality: str = "low") -> RunState:
    """Render every scene in state.animation_code to an MP4.

    Args:
        state: RunState with animation_code populated.
        quality: 'low' (480p15, fast), 'medium' (720p30), or 'high' (1080p60).

    Sets state.status = RENDERED on success, FAILED on no-scenes-rendered.
    Stores rendered video paths in state.scene_video_paths.
    """
    if not state.animation_code:
        state.error = "render_all_scenes called but state.animation_code is empty"
        state.status = RunStatus.FAILED
        return state

    run_dir = Path(config.RUNS_DIR) / state.run_id
    scenes_dir = run_dir / "scenes"
    videos_dir = run_dir / "videos"
    videos_dir.mkdir(parents=True, exist_ok=True)

    quality_flag = {"low": "-ql", "medium": "-qm", "high": "-qh"}[quality]

    rendered: dict[int, str] = {}
    failed: list[int] = []

    for scene_id in sorted(state.animation_code.keys()):
        scene_file = scenes_dir / f"scene_{scene_id:02d}.py"
        class_name = f"Scene{scene_id:02d}"

        if not scene_file.exists():
            failed.append(scene_id)
            continue

        # Run manim with the scene file. Output goes into media/videos/...
        # We use --media_dir to keep everything inside the run folder.
        media_dir = run_dir / "manim_media"
        cmd = [
            "manim", quality_flag,
            "--media_dir", str(media_dir),
            "--output_file", f"scene_{scene_id:02d}",
            str(scene_file),
            class_name,
        ]

        print(f"\n[renderer] rendering scene {scene_id} → {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"[renderer] scene {scene_id} FAILED:")
            print(result.stderr[-2000:])  # tail of stderr to keep output manageable
            failed.append(scene_id)
            # Save stderr for debugging
            (run_dir / f"render_error_scene_{scene_id:02d}.log").write_text(
                f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}",
                encoding="utf-8",
            )
            continue

        # Find the produced MP4 (manim puts it in a quality-named subdir)
        produced = _find_rendered_mp4(media_dir, f"scene_{scene_id:02d}")
        if produced is None:
            print(f"[renderer] scene {scene_id} ran but no MP4 was found")
            failed.append(scene_id)
            continue

        # Copy to canonical location for easy access
        target = videos_dir / f"scene_{scene_id:02d}.mp4"
        target.write_bytes(produced.read_bytes())
        rendered[scene_id] = str(target)
        print(f"[renderer] scene {scene_id} → {target}")

    state.scene_video_paths = rendered

    if not rendered:
        state.error = f"All {len(state.animation_code)} scenes failed to render"
        state.status = RunStatus.FAILED
    else:
        state.status = RunStatus.RENDERED
        if failed:
            state.error = f"Partial render: {len(failed)} of {len(state.animation_code)} scenes failed: {failed}"

    return state


def _find_rendered_mp4(media_dir: Path, basename: str) -> Optional[Path]:
    """Locate the MP4 that manim produced. Manim's path layout varies by version."""
    for candidate in media_dir.rglob(f"{basename}.mp4"):
        return candidate
    return None


def concatenate_videos(state: RunState) -> Optional[Path]:
    """Concatenate all rendered scene videos into a single output.

    Returns the path to the concatenated MP4, or None on failure.
    """
    if not getattr(state, "scene_video_paths", None):
        return None

    run_dir = Path(config.RUNS_DIR) / state.run_id
    concat_list = run_dir / "concat_list.txt"
    output = run_dir / "final_silent.mp4"

    # ffmpeg concat demuxer needs a file listing
    sorted_paths = [state.scene_video_paths[sid] for sid in sorted(state.scene_video_paths)]
    concat_list.write_text(
        "\n".join(f"file '{p}'" for p in sorted_paths),
        encoding="utf-8",
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(output),
    ]
    print(f"\n[renderer] concatenating {len(sorted_paths)} scenes → {output}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[renderer] concat failed:\n{result.stderr[-2000:]}")
        return None

    return output