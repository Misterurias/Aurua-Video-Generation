"""
TC6: Single-prompt baseline ablation.

This script runs the SAME task as TC2 — producing a scene plan for a backprop
explainer — but collapses the entire Aurua pipeline into ONE LLM call:

    user_question + full_source_content  ──► Claude ──► scene plan

No retrieval. No Intent agent. No separate planner. No verifier. No retry loop.
Everything the real pipeline does, the single-prompt baseline has to do in one
shot, or not at all.

The point of this ablation is to measure what the multi-agent architecture
actually buys you. If the single prompt produces a plan of equal quality, the
multi-agent system is architectural theater. If it hallucinates grounding,
misses key claims, or produces a less pedagogically coherent plan, the
verifier loop earns its complexity.

Output format matches the multi-agent RunState closely enough to support
side-by-side comparison with TC2.

Usage:
    python scripts/run_tc6_baseline.py \\
        --question "Why is the derivative of the cost with respect to a weight proportional to the activation feeding into it?" \\
        --source data/transcripts/3b1b_ch4.txt
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# Make src importable when running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config
from src.claude_client import get_client


SINGLE_PROMPT_SYSTEM = """You are an educational video planner. Given a student's question and a source transcript, produce a scene-by-scene plan for a short animated explainer video (~60-90 seconds total).

Return JSON matching this schema exactly:

{
  "scenes": [
    {
      "scene_id": <int, starting from 1>,
      "claim": "<specific claim this scene teaches>",
      "visual_goal": "<what the animation should show, in plain English>",
      "source_quote": "<a direct quote from the transcript that supports this claim>",
      "source_location": "<approximate line range in the transcript, e.g. 'L40-L50'>",
      "duration_sec": <int between 5 and 30>
    }
  ]
}

Rules:
1. Each scene teaches exactly one claim.
2. Each claim must be supported by a specific quote from the source transcript.
3. visual_goal must describe something renderable in Manim with basic primitives.
4. Total duration 60-90 seconds, typically 3-5 scenes.
5. Pedagogical flow: context first, then mechanism, then example.

Return only the JSON. No prose, no markdown fences.
"""


def run_baseline(question: str, source_path: Path) -> dict:
    source_content = source_path.read_text(encoding="utf-8")

    # Number the source lines so the model CAN cite specific locations if it
    # chooses to. This is a generous affordance for the baseline — real
    # single-prompt users typically wouldn't do this — but it gives the
    # comparison more credibility.
    numbered_source = "\n".join(
        f"L{i:03d}  {line}"
        for i, line in enumerate(source_content.splitlines(), start=1)
    )

    user_prompt = (
        f"Student's question:\n{question}\n\n"
        f"Source transcript (line-numbered):\n{numbered_source}\n\n"
        "Produce the scene plan JSON described in your instructions."
    )

    client = get_client()
    start = time.time()

    response = client.messages.create(
        model=config.AGENT_MODEL,
        max_tokens=config.MAX_TOKENS,
        temperature=config.AGENT_TEMPERATURE,
        system=SINGLE_PROMPT_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    )

    elapsed = time.time() - start
    raw_text = "".join(b.text for b in response.content if getattr(b, "type", None) == "text")

    # Extract JSON, tolerating fences
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", raw_text, re.DOTALL)
    candidate = match.group(1) if match else raw_text.strip()

    try:
        parsed = json.loads(candidate)
        parse_error = None
    except json.JSONDecodeError as e:
        parsed = None
        parse_error = str(e)

    return {
        "run_id": f"tc6_{uuid4().hex[:8]}",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "test_case_id": "TC6",
        "approach": "single_prompt_baseline",
        "user_question": question,
        "source_path": str(source_path),
        "system_prompt": SINGLE_PROMPT_SYSTEM,
        "user_prompt_length_chars": len(user_prompt),
        "response_raw": raw_text,
        "response_parsed": parsed,
        "parse_error": parse_error,
        "cost": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "api_calls": 1,
            "wall_clock_sec": elapsed,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", required=True)
    parser.add_argument("--source", required=True, type=Path)
    args = parser.parse_args()

    result = run_baseline(args.question, args.source)

    run_dir = Path(config.RUNS_DIR) / result["run_id"]
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "state.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"\nRun ID: {result['run_id']}")
    print(f"Approach: single-prompt baseline (no retrieval, no verifier)")
    print(f"Cost: {result['cost']['input_tokens']} in, "
          f"{result['cost']['output_tokens']} out in 1 call "
          f"({result['cost']['wall_clock_sec']:.2f}s)")

    if result["parse_error"]:
        print(f"\nPARSE ERROR: {result['parse_error']}")
        print(f"Raw response (first 500 chars):\n{result['response_raw'][:500]}")
    elif result["response_parsed"] and "scenes" in result["response_parsed"]:
        scenes = result["response_parsed"]["scenes"]
        total = sum(s.get("duration_sec", 0) for s in scenes)
        print(f"\nPlan: {len(scenes)} scenes, {total}s total")
        for scene in scenes:
            print(f"\n  [Scene {scene.get('scene_id')}] {scene.get('claim', '')[:120]}")
            print(f"    source quote: \"{(scene.get('source_quote') or '')[:100]}...\"")
            print(f"    source location: {scene.get('source_location', '—')}")
            print(f"    visual: {(scene.get('visual_goal') or '')[:100]}...")
            print(f"    duration: {scene.get('duration_sec')}s")

    print(f"\nFull result saved to: {run_dir / 'state.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())