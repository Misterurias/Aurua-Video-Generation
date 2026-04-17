"""
Shared state for a single Aurua run.

Every agent reads from and writes to a RunState instance. The state is
serializable to JSON so full runs can be saved for evaluation and replay.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Agent 1 outputs
# -----------------------------------------------------------------------------

ConfusionType = Literal["mechanical", "conceptual", "vague"]


class SourceSpan(BaseModel):
    """A retrieved chunk of source content with provenance."""
    span_id: str
    text: str
    location: str  # e.g. "3b1b_ch4.txt:L42-L58"
    retrieval_score: float


class IntentOutput(BaseModel):
    confusion_type: ConfusionType
    learning_goal: str
    relevant_spans: list[SourceSpan]
    key_claims_to_explain: list[str]
    # When confusion_type is "vague", downstream agents should halt and
    # prompt the user for clarification instead of fabricating a plan.
    clarification_question: Optional[str] = None


# -----------------------------------------------------------------------------
# Agent 2 outputs
# -----------------------------------------------------------------------------

class Scene(BaseModel):
    scene_id: int
    claim: str
    visual_goal: str
    source_ref: str  # span_id that grounds this claim
    duration_sec: int = Field(ge=5, le=30)


class ScenePlan(BaseModel):
    scenes: list[Scene]

    @property
    def total_duration_sec(self) -> int:
        return sum(s.duration_sec for s in self.scenes)


# -----------------------------------------------------------------------------
# Agent 3 outputs
# -----------------------------------------------------------------------------

class ClaimVerdict(BaseModel):
    scene_id: int
    grounded: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reason: Optional[str] = None  # populated when grounded=False


class VerificationResult(BaseModel):
    verdict: Literal["pass", "revise"]
    per_claim_results: list[ClaimVerdict]
    retry_count: int

    @property
    def failed_scene_ids(self) -> list[int]:
        return [c.scene_id for c in self.per_claim_results if not c.grounded]


# -----------------------------------------------------------------------------
# Cost tracking
# -----------------------------------------------------------------------------

class CostTracker(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    api_calls: int = 0
    wall_clock_sec: float = 0.0

    def add(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.api_calls += 1


# -----------------------------------------------------------------------------
# Top-level run state
# -----------------------------------------------------------------------------

class RunStatus(str, Enum):
    PENDING = "pending"
    INTENT_COMPLETE = "intent_complete"
    PLAN_COMPLETE = "plan_complete"
    VERIFIED = "verified"
    VERIFICATION_EXHAUSTED = "verification_exhausted"
    CLARIFICATION_REQUIRED = "clarification_required"
    CODE_COMPLETE = "code_complete"
    NARRATION_COMPLETE = "narration_complete"
    RENDERED = "rendered"
    FAILED = "failed"


class RunState(BaseModel):
    # Identity
    run_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    started_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # Inputs
    user_question: str
    source_path: str  # path to transcript file
    source_content: str

    # Agent outputs
    intent_output: Optional[IntentOutput] = None
    scene_plan: Optional[ScenePlan] = None
    verification_history: list[VerificationResult] = Field(default_factory=list)
    animation_code: dict[int, str] = Field(default_factory=dict)  # scene_id -> code
    narration_script: Optional[str] = None

    # Bookkeeping
    status: RunStatus = RunStatus.PENDING
    error: Optional[str] = None
    cost: CostTracker = Field(default_factory=CostTracker)

    def latest_verification(self) -> Optional[VerificationResult]:
        return self.verification_history[-1] if self.verification_history else None

    def retries_used(self) -> int:
        return max(0, len(self.verification_history) - 1)
