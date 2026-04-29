"""
Orchestrator for an Aurua run.

Wires the agents together:

    Intent → Planner → Verifier ─(pass)─→ done (Phase 2 stopping point)
                         │
                         └─(revise)─→ Planner → Verifier → ...
                                      (up to MAX_VERIFIER_RETRIES times)

On exhaustion the state is marked VERIFICATION_EXHAUSTED rather than failed —
downstream orchestration (Phase 3) decides whether to drop the ungrounded
scenes, surface them to the user, or halt.

Phase 3 will extend this with the parallel Animation Coder + Narration Writer
branch and the deterministic Renderer.
"""
from __future__ import annotations

import json
import traceback
from pathlib import Path

from . import config
from .agents.intent_grounding import run_intent_agent
from .agents.planner import run_planner_agent
from .agents.verifier import run_verifier_agent
from .state import RunState, RunStatus
from .tools.retrieval import Retriever, get_or_build_retriever


def run_pipeline(
    *,
    user_question: str,
    source_path: Path,
    retriever: Retriever | None = None,
) -> RunState:
    """Run the full Phase 2 pipeline (Intent → Planner → Verifier loop)."""
    source_content = source_path.read_text(encoding="utf-8")
    state = RunState(
        user_question=user_question,
        source_path=str(source_path),
        source_content=source_content,
    )

    if retriever is None:
        retriever = get_or_build_retriever([source_path])

    try:
        # --- Agent 1: Intent & Grounding ---
        state = run_intent_agent(state, retriever)
        if state.status == RunStatus.CLARIFICATION_REQUIRED:
            _save_state(state)
            return state  # stop — the UI/caller should ask the clarifying question

        # --- Agent 2 / Agent 3 loop ---
        state = run_planner_agent(state)
        state = run_verifier_agent(state)

        while (
            state.status == RunStatus.PLAN_COMPLETE  # verifier set this → revise
            and state.retries_used() < config.MAX_VERIFIER_RETRIES
        ):
            latest_feedback = state.latest_verification()
            state = run_planner_agent(state, verifier_feedback=latest_feedback)
            state = run_verifier_agent(state)

        # After the loop, state.status is one of:
        #   VERIFIED                  — success
        #   VERIFICATION_EXHAUSTED    — retries used, some claims still ungrounded
        #   CLARIFICATION_REQUIRED    — handled above, unreachable here
        
        # --- Phase 3: Animation Coder + Renderer ---
        # Only run rendering if verification passed cleanly.
        if state.status == RunStatus.VERIFIED:
            from .agents.animation_coder import run_animation_coder
            from .tools.renderer import render_all_scenes, concatenate_videos

            state = run_animation_coder(state)

            if state.status == RunStatus.CODE_COMPLETE:
                state = render_all_scenes(state, quality="low")
                if state.status == RunStatus.RENDERED:
                    final = concatenate_videos(state)
                    if final:
                        print(f"\n[run] final silent video: {final}")
                        
    except Exception as exc:  # noqa: BLE001
        state.status = RunStatus.FAILED
        state.error = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"

    _save_state(state)
    return state


def _save_state(state: RunState) -> None:
    """Persist the full run state for evaluation and replay."""
    run_dir = Path(config.RUNS_DIR) / state.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "state.json").write_text(
        state.model_dump_json(indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run the Aurua Phase 2 pipeline.")
    parser.add_argument(
        "--question", required=True,
        help="The student's question about the source content.",
    )
    parser.add_argument(
        "--source", required=True, type=Path,
        help="Path to the source transcript (e.g., data/transcripts/3b1b_ch4.txt).",
    )
    args = parser.parse_args()

    state = run_pipeline(user_question=args.question, source_path=args.source)

    print(f"\nRun ID: {state.run_id}")
    print(f"Status: {state.status.value}")
    print(f"Retries used: {state.retries_used()}")
    print(
        f"Cost: {state.cost.input_tokens} in, {state.cost.output_tokens} out "
        f"across {state.cost.api_calls} calls "
        f"({state.cost.wall_clock_sec:.2f}s)"
    )

    if state.error:
        print(f"\nERROR:\n{state.error}")
    elif state.status == RunStatus.CLARIFICATION_REQUIRED and state.intent_output:
        print(f"\nNeeds clarification: {state.intent_output.clarification_question}")
    elif state.scene_plan:
        print(f"\nFinal plan ({len(state.scene_plan.scenes)} scenes, "
              f"{state.scene_plan.total_duration_sec}s total):")
        for scene in state.scene_plan.scenes:
            print(f"  [Scene {scene.scene_id}] {scene.claim}")
            print(f"    visual: {scene.visual_goal}")
            print(f"    source: {scene.source_ref} ({scene.duration_sec}s)")

    print(f"\nFull state saved to: {Path(config.RUNS_DIR) / state.run_id}/state.json")
    print(f"Traces saved to: {Path(config.TRACES_DIR) / state.run_id}/")


if __name__ == "__main__":
    _cli()
