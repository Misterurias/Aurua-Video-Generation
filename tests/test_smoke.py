"""
Smoke tests — verify that modules import cleanly and core types work.

Run with: pytest tests/

These do NOT make API calls. They catch import errors, schema mistakes,
and orchestration bugs before you spend tokens.
"""
from __future__ import annotations

import json

import pytest

from src.state import (
    ClaimVerdict,
    CostTracker,
    IntentOutput,
    RunState,
    RunStatus,
    Scene,
    ScenePlan,
    SourceSpan,
    VerificationResult,
)


def test_empty_run_state_roundtrips():
    state = RunState(
        user_question="Why does backprop work?",
        source_path="data/transcripts/3b1b_ch4.txt",
        source_content="placeholder",
    )
    payload = state.model_dump_json()
    restored = RunState.model_validate_json(payload)
    assert restored.user_question == state.user_question
    assert restored.status == RunStatus.PENDING


def test_intent_output_with_vague_confusion():
    intent = IntentOutput(
        confusion_type="vague",
        learning_goal="Unclear from question",
        relevant_spans=[],
        key_claims_to_explain=[],
        clarification_question="Which part of backprop are you stuck on?",
    )
    assert intent.clarification_question is not None


def test_scene_plan_total_duration():
    plan = ScenePlan(
        scenes=[
            Scene(scene_id=1, claim="c1", visual_goal="v1", source_ref="s1", duration_sec=15),
            Scene(scene_id=2, claim="c2", visual_goal="v2", source_ref="s2", duration_sec=20),
        ]
    )
    assert plan.total_duration_sec == 35


def test_scene_duration_bounds():
    with pytest.raises(Exception):
        Scene(scene_id=1, claim="c", visual_goal="v", source_ref="s", duration_sec=3)  # < 5
    with pytest.raises(Exception):
        Scene(scene_id=1, claim="c", visual_goal="v", source_ref="s", duration_sec=45)  # > 30


def test_verification_result_failed_scene_ids():
    result = VerificationResult(
        verdict="revise",
        per_claim_results=[
            ClaimVerdict(scene_id=1, grounded=True, confidence=0.9),
            ClaimVerdict(scene_id=2, grounded=False, confidence=0.9, reason="no source"),
            ClaimVerdict(scene_id=3, grounded=False, confidence=0.7, reason="wrong span"),
        ],
        retry_count=0,
    )
    assert result.failed_scene_ids == [2, 3]


def test_cost_tracker_accumulates():
    cost = CostTracker()
    cost.add(input_tokens=100, output_tokens=50)
    cost.add(input_tokens=200, output_tokens=75)
    assert cost.input_tokens == 300
    assert cost.output_tokens == 125
    assert cost.api_calls == 2


def test_run_state_retries_used():
    state = RunState(
        user_question="q", source_path="p", source_content="c",
    )
    assert state.retries_used() == 0

    # Simulate initial verification + two retries = 3 entries, 2 retries used
    for i in range(3):
        state.verification_history.append(
            VerificationResult(
                verdict="revise",
                per_claim_results=[ClaimVerdict(scene_id=1, grounded=False, confidence=0.8, reason="x")],
                retry_count=i,
            )
        )
    assert state.retries_used() == 2


def test_all_agents_importable():
    """Catch syntax errors and circular imports without making API calls."""
    from src.agents import intent_grounding, planner, verifier, narration_writer  # noqa: F401
    from src import run, claude_client, config  # noqa: F401
    from src.tools import retrieval  # noqa: F401
    from src.prompts import intent, planner as planner_prompt, verifier as verifier_prompt  # noqa: F401
    from src.prompts import narration, animation_coder  # noqa: F401


def test_source_span_serializes():
    span = SourceSpan(
        span_id="abc123",
        text="the derivative with respect to the weight...",
        location="3b1b_ch4.txt:L42-L58",
        retrieval_score=0.87,
    )
    payload = json.loads(span.model_dump_json())
    assert payload["span_id"] == "abc123"
    assert payload["retrieval_score"] == 0.87
