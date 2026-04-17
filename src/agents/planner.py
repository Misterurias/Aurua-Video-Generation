"""Agent 2: Explanation Planner."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .. import config
from ..claude_client import call_claude_structured
from ..prompts.planner import PLANNER_SYSTEM_PROMPT
from ..state import RunState, RunStatus, ScenePlan, VerificationResult


def run_planner_agent(
    state: RunState,
    verifier_feedback: Optional[VerificationResult] = None,
) -> RunState:
    """Produce (or revise) a scene plan grounded in the intent output.

    When called for the first time, verifier_feedback is None. On subsequent
    calls (retries), verifier_feedback contains the flagged scenes and reasons.
    """
    if state.intent_output is None:
        raise RuntimeError("Planner called before Intent agent produced output.")

    prompt_payload = {
        "learning_goal": state.intent_output.learning_goal,
        "relevant_spans": [s.model_dump() for s in state.intent_output.relevant_spans],
        "key_claims_to_explain": state.intent_output.key_claims_to_explain,
    }

    if verifier_feedback is not None:
        prompt_payload["previous_plan"] = (
            state.scene_plan.model_dump() if state.scene_plan else None
        )
        prompt_payload["verifier_feedback"] = verifier_feedback.model_dump()
        user_prompt = (
            "The previous plan failed verification. Revise ONLY the flagged scenes.\n\n"
            f"{json.dumps(prompt_payload, indent=2)}\n\n"
            "Return the full revised JSON plan."
        )
        trace_label = f"02_planner_retry_{verifier_feedback.retry_count}"
    else:
        user_prompt = (
            f"Plan an explainer for the following:\n\n"
            f"{json.dumps(prompt_payload, indent=2)}\n\n"
            f"Return the JSON plan."
        )
        trace_label = "02_planner_initial"

    trace_dir = Path(config.TRACES_DIR) / state.run_id

    plan = call_claude_structured(
        system_prompt=PLANNER_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_model=ScenePlan,
        cost_tracker=state.cost,
        trace_label=trace_label,
        trace_dir=trace_dir,
    )

    state.scene_plan = plan
    state.status = RunStatus.PLAN_COMPLETE
    return state
