"""
Thin wrapper around the Anthropic SDK.

Every agent calls `call_claude(...)` instead of the SDK directly so that:
  - cost tracking happens in one place
  - JSON parsing is consistent
  - traces can be logged for evaluation
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Optional, TypeVar

from anthropic import Anthropic
from pydantic import BaseModel, ValidationError

from . import config
from .state import CostTracker

T = TypeVar("T", bound=BaseModel)

_client: Optional[Anthropic] = None


def get_client() -> Anthropic:
    global _client
    if _client is None:
        if not config.ANTHROPIC_API_KEY:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env "
                "and fill in your key."
            )
        _client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def call_claude(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str = config.AGENT_MODEL,
    temperature: float = config.AGENT_TEMPERATURE,
    max_tokens: int = config.MAX_TOKENS,
    cost_tracker: Optional[CostTracker] = None,
    trace_label: Optional[str] = None,
    trace_dir: Optional[Path] = None,
) -> str:
    """Make a single Claude API call and return the raw text response."""
    client = get_client()
    start = time.time()

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    elapsed = time.time() - start

    text = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )

    if cost_tracker is not None:
        cost_tracker.add(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
        cost_tracker.wall_clock_sec += elapsed

    if config.ENABLE_TRACE_LOGGING and trace_label and trace_dir:
        _write_trace(trace_dir, trace_label, system_prompt, user_prompt, text)

    return text


def call_claude_structured(
    *,
    system_prompt: str,
    user_prompt: str,
    response_model: type[T],
    model: str = config.AGENT_MODEL,
    temperature: float = config.AGENT_TEMPERATURE,
    cost_tracker: Optional[CostTracker] = None,
    trace_label: Optional[str] = None,
    trace_dir: Optional[Path] = None,
    max_parse_retries: int = 1,
) -> T:
    """
    Call Claude and parse the response into a Pydantic model.

    The system prompt should instruct Claude to return JSON matching the
    model's schema. If parsing fails, we retry once with an error message
    telling Claude what broke.
    """
    last_error: Optional[str] = None

    for attempt in range(max_parse_retries + 1):
        effective_user_prompt = user_prompt
        if last_error is not None:
            effective_user_prompt = (
                f"{user_prompt}\n\n"
                f"Your previous response could not be parsed. Error:\n{last_error}\n"
                "Return valid JSON matching the schema exactly."
            )

        raw = call_claude(
            system_prompt=system_prompt,
            user_prompt=effective_user_prompt,
            model=model,
            temperature=temperature,
            cost_tracker=cost_tracker,
            trace_label=trace_label,
            trace_dir=trace_dir,
        )

        try:
            payload = _extract_json(raw)
            return response_model.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = str(exc)
            if attempt == max_parse_retries:
                raise RuntimeError(
                    f"Failed to parse {response_model.__name__} after "
                    f"{max_parse_retries + 1} attempts. Last error: {last_error}\n"
                    f"Raw response:\n{raw}"
                ) from exc

    raise AssertionError("unreachable")  # pragma: no cover


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def _extract_json(text: str) -> dict:
    """Extract JSON from a Claude response, tolerating markdown fences."""
    match = _JSON_FENCE_RE.search(text)
    candidate = match.group(1) if match else text.strip()
    return json.loads(candidate)


def _write_trace(
    trace_dir: Path,
    label: str,
    system_prompt: str,
    user_prompt: str,
    response: str,
) -> None:
    trace_dir.mkdir(parents=True, exist_ok=True)
    trace_path = trace_dir / f"{label}.txt"
    with trace_path.open("a", encoding="utf-8") as f:
        f.write(f"\n{'=' * 70}\n")
        f.write(f"TRACE: {label}  @  {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'=' * 70}\n")
        f.write(f"\n--- SYSTEM ---\n{system_prompt}\n")
        f.write(f"\n--- USER ---\n{user_prompt}\n")
        f.write(f"\n--- RESPONSE ---\n{response}\n")
