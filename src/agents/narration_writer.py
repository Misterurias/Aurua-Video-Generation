"""Agent 4b: Narration Writer.

Scaffolded for Phase 3. The prompt is ready; wire this into run.py once the
verifier loop is fully evaluated in Phase 2. Runs in parallel with the
Animation Coder — both take the verified scene plan and produce independent
outputs that the Renderer combines.
"""
from __future__ import annotations

import json
from pathlib import Path

from .. import config
from ..claude_client import call_claude
from ..prompts.narration import NARRATION_SYSTEM_PROMPT
from ..state import RunState, RunStatus


def run_narration_agent(state: RunState) -> RunState:
    if state.scene_plan is None:
        raise RuntimeError("Narration agent called before a verified plan exists.")
    if state.status != RunStatus.VERIFIED:
        raise RuntimeError(
            f"Narration agent called from invalid status: {state.status.value}. "
            "Expected VERIFIED."
        )

    spans = (
        [s.model_dump() for s in state.intent_output.relevant_spans]
        if state.intent_output else []
    )

    payload = {
        "scene_plan": state.scene_plan.model_dump(),
        "relevant_spans": spans,
    }

    user_prompt = (
        "Write the narration script for the following verified plan. "
        "Follow the timing-marker format exactly.\n\n"
        f"{json.dumps(payload, indent=2)}"
    )

    trace_dir = Path(config.TRACES_DIR) / state.run_id

    script = call_claude(
        system_prompt=NARRATION_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        cost_tracker=state.cost,
        trace_label="04b_narration",
        trace_dir=trace_dir,
    )

    state.narration_script = script.strip()
    state.status = RunStatus.NARRATION_COMPLETE
    return state
