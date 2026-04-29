"""Agent 4a: Animation Coder.

Takes a verified scene plan and generates Manim code for each scene.
One Claude call per scene, sequential for trace clarity.

Writes generated code to outputs/runs/<run_id>/scenes/scene_NN.py
where the Renderer (deterministic tool) picks them up.
"""
from __future__ import annotations

import re
from pathlib import Path

from ..claude_client import call_claude
from ..prompts.animation_coder import ANIMATION_CODER_SYSTEM_PROMPT
from ..state import RunState, RunStatus, Scene
from .. import config


def run_animation_coder(state: RunState) -> RunState:
    """Generate Manim code for each scene in the verified plan."""
    if state.scene_plan is None or state.status != RunStatus.VERIFIED:
        # Don't generate code for unverified plans — that's the whole point
        # of having the verifier in the first place.
        return state

    scenes_dir = Path(config.RUNS_DIR) / state.run_id / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)

    trace_dir = Path(config.TRACES_DIR) / state.run_id

    for scene in state.scene_plan.scenes:
        code = _generate_scene_code(scene, state, trace_dir)
        state.animation_code[scene.scene_id] = code

        # Write to disk for the Renderer
        scene_file = scenes_dir / f"scene_{scene.scene_id:02d}.py"
        scene_file.write_text(code, encoding="utf-8")

    state.status = RunStatus.CODE_COMPLETE
    return state


def _generate_scene_code(scene: Scene, state: RunState, trace_dir: Path) -> str:
    """Single Claude call for one scene."""
    user_prompt = (
        f"Generate Manim code for this scene.\n\n"
        f"scene_id: {scene.scene_id}\n"
        f"claim: {scene.claim}\n"
        f"visual_goal: {scene.visual_goal}\n"
        f"duration_sec: {scene.duration_sec}\n\n"
        f"Class name: Scene{scene.scene_id:02d}\n"
        f"Output file will be: scene_{scene.scene_id:02d}.py\n\n"
        f"Return ONLY the complete Python file content. No markdown fences."
    )

    raw = call_claude(
        system_prompt=ANIMATION_CODER_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model=config.CODER_MODEL,
        temperature=config.CODER_TEMPERATURE,
        cost_tracker=state.cost,
        trace_label=f"04a_animation_coder_scene_{scene.scene_id:02d}",
        trace_dir=trace_dir,
    )

    return _strip_code_fences(raw)


_FENCE_RE = re.compile(r"^```(?:python|py)?\s*\n(.*?)\n```\s*$", re.DOTALL)


def _strip_code_fences(text: str) -> str:
    """Remove ```python ... ``` wrappers if Claude added them despite instructions."""
    text = text.strip()
    match = _FENCE_RE.match(text)
    if match:
        return match.group(1).strip()
    return text