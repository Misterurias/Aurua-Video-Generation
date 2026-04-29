# """Agent 1: Intent & Grounding."""
# from __future__ import annotations

# import json

# from ..claude_client import call_claude_structured
# from ..prompts.intent import INTENT_SYSTEM_PROMPT
# from ..state import IntentOutput, RunState, RunStatus, SourceSpan
# from ..tools.retrieval import Retriever
# from .. import config


# def run_intent_agent(state: RunState, retriever: Retriever) -> RunState:
#     """Retrieve spans, then ask Claude to identify confusion and key claims."""
#     # 1. Retrieval
#     hits = retriever.search(state.user_question, top_k=config.TOP_K_RETRIEVAL)

#     retrieved_spans_for_prompt = [
#         {
#             "span_id": hit.chunk.chunk_id,
#             "text": hit.chunk.text,
#             "location": hit.chunk.location,
#             "retrieval_score": round(hit.score, 4),
#         }
#         for hit in hits
#     ]

#     # 2. Ask Claude to structure the intent
#     user_prompt = (
#         f"Student's question:\n{state.user_question}\n\n"
#         f"Retrieved source spans:\n{json.dumps(retrieved_spans_for_prompt, indent=2)}\n\n"
#         f"Produce the JSON described in your instructions."
#     )

#     from pathlib import Path
#     trace_dir = Path(config.TRACES_DIR) / state.run_id

#     intent = call_claude_structured(
#         system_prompt=INTENT_SYSTEM_PROMPT,
#         user_prompt=user_prompt,
#         response_model=IntentOutput,
#         cost_tracker=state.cost,
#         trace_label="01_intent",
#         trace_dir=trace_dir,
#     )

#     state.intent_output = intent

#     if intent.confusion_type == "vague":
#         state.status = RunStatus.CLARIFICATION_REQUIRED
#     else:
#         state.status = RunStatus.INTENT_COMPLETE

#     return state


"""Agent 1: Intent & Grounding.

v0.3: Adds query expansion before retrieval to address Phase 2 F1/F2
retrieval-coverage failures. The user's question is paraphrased into
N variants by Claude; each variant is embedded and used as a FAISS
query; results are deduplicated by span_id and ranked by max score.
"""
from __future__ import annotations

import json
from pathlib import Path

from ..claude_client import call_claude_structured
from ..prompts.intent import INTENT_SYSTEM_PROMPT
from ..state import IntentOutput, RunState, RunStatus
from ..tools.retrieval import Retriever
from .. import config


# ---------------------------------------------------------------------------
# Query expansion (v0.3)
# ---------------------------------------------------------------------------
from pydantic import BaseModel


class _QueryVariants(BaseModel):
    variants: list[str]


_QUERY_EXPANSION_SYSTEM = """You are a query expansion assistant for a retrieval system.

Given a student's question about a technical topic, generate paraphrased
variants that capture different ways the same question might be asked. Use
technical synonyms, alternative phrasings, and rephrase from different angles
(definition, mechanism, justification, example).

Return ONLY a JSON object with this exact schema:
{"variants": ["variant 1", "variant 2", "variant 3"]}

Rules:
- Generate exactly the number of variants requested.
- Each variant must be a complete question, not a phrase.
- Each variant must be semantically equivalent to the original — no new topics.
- Vary vocabulary aggressively. If the original uses "derivative", a variant might use "rate of change" or "sensitivity".
"""


def _expand_query(question: str, state: RunState) -> list[str]:
    """Return [original] + N paraphrased variants. On failure, returns [original]."""
    if not config.ENABLE_QUERY_EXPANSION:
        return [question]

    user_prompt = (
        f"Original question: {question}\n\n"
        f"Generate exactly {config.QUERY_EXPANSION_VARIANTS} paraphrased variants."
    )

    trace_dir = Path(config.TRACES_DIR) / state.run_id

    try:
        result = call_claude_structured(
            system_prompt=_QUERY_EXPANSION_SYSTEM,
            user_prompt=user_prompt,
            response_model=_QueryVariants,
            cost_tracker=state.cost,
            trace_label="00_query_expansion",
            trace_dir=trace_dir,
        )
        return [question] + result.variants
    except Exception as exc:  # noqa: BLE001
        # Don't fail the pipeline over query expansion — fall back to single query.
        print(f"[query expansion failed: {exc}] — falling back to original question only")
        return [question]


# ---------------------------------------------------------------------------
# Multi-query retrieval
# ---------------------------------------------------------------------------
def _multi_query_retrieve(retriever: Retriever, queries: list[str], top_k: int) -> list:
    """Run retrieval for each query, dedupe by span_id, rank by max score."""
    seen: dict[str, object] = {}  # span_id -> hit (with the highest score so far)
    for q in queries:
        for hit in retriever.search(q, top_k=top_k):
            sid = hit.chunk.chunk_id
            if sid not in seen or hit.score > seen[sid].score:
                seen[sid] = hit
    # Sort by score descending, take top_k overall
    ranked = sorted(seen.values(), key=lambda h: h.score, reverse=True)
    return ranked[:top_k]


# ---------------------------------------------------------------------------
# Main agent entry point
# ---------------------------------------------------------------------------
def run_intent_agent(state: RunState, retriever: Retriever) -> RunState:
    """Retrieve spans (with query expansion), then identify confusion + key claims."""
    # 1. Query expansion (v0.3)
    queries = _expand_query(state.user_question, state)

    # 2. Multi-query retrieval with dedup
    hits = _multi_query_retrieve(retriever, queries, top_k=config.TOP_K_RETRIEVAL)

    retrieved_spans_for_prompt = [
        {
            "span_id": hit.chunk.chunk_id,
            "text": hit.chunk.text,
            "location": hit.chunk.location,
            "retrieval_score": round(hit.score, 4),
        }
        for hit in hits
    ]

    # 3. Ask Claude to structure the intent
    user_prompt = (
        f"Student's question:\n{state.user_question}\n\n"
        f"Retrieved source spans (top {len(hits)} after query expansion + dedup):\n"
        f"{json.dumps(retrieved_spans_for_prompt, indent=2)}\n\n"
        f"Produce the JSON described in your instructions."
    )

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