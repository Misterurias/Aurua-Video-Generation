"""Agent 1: Intent & Grounding."""
from __future__ import annotations

import json

from ..claude_client import call_claude_structured
from ..prompts.intent import INTENT_SYSTEM_PROMPT
from ..state import IntentOutput, RunState, RunStatus, SourceSpan
from ..tools.retrieval import Retriever
from .. import config


def run_intent_agent(state: RunState, retriever: Retriever) -> RunState:
    """Retrieve spans, then ask Claude to identify confusion and key claims."""
    # 1. Retrieval
    hits = retriever.search(state.user_question, top_k=config.TOP_K_RETRIEVAL)

    retrieved_spans_for_prompt = [
        {
            "span_id": hit.chunk.chunk_id,
            "text": hit.chunk.text,
            "location": hit.chunk.location,
            "retrieval_score": round(hit.score, 4),
        }
        for hit in hits
    ]

    # 2. Ask Claude to structure the intent
    user_prompt = (
        f"Student's question:\n{state.user_question}\n\n"
        f"Retrieved source spans:\n{json.dumps(retrieved_spans_for_prompt, indent=2)}\n\n"
        f"Produce the JSON described in your instructions."
    )

    from pathlib import Path
    trace_dir = Path(config.TRACES_DIR) / state.run_id

    intent = call_claude_structured(
        system_prompt=INTENT_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_model=IntentOutput,
        cost_tracker=state.cost,
        trace_label="01_intent",
        trace_dir=trace_dir,
    )

    state.intent_output = intent

    if intent.confusion_type == "vague":
        state.status = RunStatus.CLARIFICATION_REQUIRED
    else:
        state.status = RunStatus.INTENT_COMPLETE

    return state
