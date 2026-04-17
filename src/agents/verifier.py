"""Agent 3: Grounding Verifier.

This is the agent that makes Aurua genuinely agentic rather than a prompt chain.
A separate verifier with a distinct system prompt catches errors the Planner
does not catch when asked to self-check, and the verify→revise→re-verify loop
is coordination a single LLM call cannot replicate.
"""
from __future__ import annotations

import json
from pathlib import Path

from .. import config
from ..claude_client import call_claude_structured
from ..prompts.verifier import VERIFIER_SYSTEM_PROMPT
from ..state import RunState, RunStatus, VerificationResult


def run_verifier_agent(state: RunState) -> RunState:
    """Check each scene's claim against its cited source span."""
    if state.scene_plan is None:
        raise RuntimeError("Verifier called before Planner produced a plan.")
    if state.intent_output is None:
        raise RuntimeError("Verifier called before Intent produced spans.")

    retry_count = len(state.verification_history)

    prompt_payload = {
        "scene_plan": state.scene_plan.model_dump(),
        "relevant_spans": [s.model_dump() for s in state.intent_output.relevant_spans],
        "retry_count": retry_count,
    }

    user_prompt = (
        "Verify each scene against its cited source span.\n\n"
        f"{json.dumps(prompt_payload, indent=2)}\n\n"
        "Return the JSON verdict."
    )

    trace_dir = Path(config.TRACES_DIR) / state.run_id

    result = call_claude_structured(
        system_prompt=VERIFIER_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_model=VerificationResult,
        model=config.VERIFIER_MODEL,
        cost_tracker=state.cost,
        trace_label=f"03_verifier_attempt_{retry_count}",
        trace_dir=trace_dir,
    )

    state.verification_history.append(result)

    if result.verdict == "pass":
        state.status = RunStatus.VERIFIED
    elif retry_count >= config.MAX_VERIFIER_RETRIES:
        # Exhausted retries — downstream orchestration decides what to do.
        state.status = RunStatus.VERIFICATION_EXHAUSTED
    else:
        # Stay in PLAN_COMPLETE so the orchestrator knows to re-plan
        state.status = RunStatus.PLAN_COMPLETE

    return state
