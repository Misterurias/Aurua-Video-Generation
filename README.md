# Aurua

An agentic system that turns a confusing educational passage plus a student's question into a short animated explainer video. Course project for 94815 Agentic Technologies, CMU Heinz College.

**Team:** Jorge Urias (individual project)
**Track:** Track A — Technical Build
**Status (Phase 2):** Agents 1–3 implemented and evaluated on 5 test cases plus 1 ablation. Rendering branch (Agents 4a/4b + Renderer) is Phase 3 work.

## What it does (Phase 2)

Given a source transcript and a student question, the implemented pipeline:

1. Embeds the transcript once into a FAISS index (cached).
2. Retrieves relevant source spans for the question.
3. Classifies the confusion as `mechanical`, `conceptual`, or `vague`. Vague classification short-circuits the pipeline with a clarifying question.
4. Plans a scene-by-scene explainer (~60–90 seconds) with per-scene grounding references.
5. Verifies each scene's claim against its cited source span using a second LLM with a distinct system prompt.
6. If any scene fails verification, revises only the flagged scenes and re-verifies. Up to 2 retries.

The verifier retry loop is the piece that makes this genuinely agentic rather than a prompt chain. Phase 3 will add the animation-coder and narration branches, plus the Manim/TTS/ffmpeg renderer.

## Architecture

```
User question + source content
        ↓
[Agent 1] Intent & Grounding   ── retrieval tool (FAISS + sentence-transformers)
        ↓
        ├─(vague)─► clarify → stop
        ↓
[Agent 2] Explanation Planner  ←─── (revise with feedback)
        ↓                            ↑
[Agent 3] Grounding Verifier  ──────┘
        ↓ (pass)
[Phase 3: 4a Animation + 4b Narration in parallel, then deterministic Renderer]
```

Full architecture discussion including role justifications and coordination logic is in `docs/phase_2_document.pdf` §3.

## Setup

Requirements: Python 3.11+ and an Anthropic API key.

```bash
cd aurua
python -m venv .venv
source .venv/bin/activate        # macOS/Linux; .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env             # edit .env and add your ANTHROPIC_API_KEY
```

Transcripts are already populated in `data/transcripts/` — see `data/transcripts/SOURCES.md` for provenance.

On first run, the retriever builds a FAISS index (~10 seconds) and caches it in `data/index/`. Delete that directory to force a rebuild if you change transcripts.

## Running the pipeline

Multi-agent pipeline (primary):

```bash
python -m src.run \
  --question "Why is the derivative of the cost with respect to a weight proportional to the activation feeding into it?" \
  --source data/transcripts/3b1b_ch4.txt
```

Single-prompt baseline (TC6 ablation):

```bash
python scripts/run_tc6_baseline.py \
  --question "..." \
  --source data/transcripts/3b1b_ch4.txt
```

Output:
- Console: final plan (or clarification question) and cost/latency metrics.
- `outputs/runs/{run_id}/state.json`: full run state.
- `eval/traces/{run_id}/`: per-call prompt/response traces, one file per agent call.

## Evaluation

All six test cases have been executed. Results are in `eval/evaluation_results.csv`; failure analysis is in `eval/failure_log.md`; configuration and version tracking are in `eval/version_notes.md`; test definitions are in `eval/test_cases.csv`.

Summary of results (v0.2, 2026-04-16):

| Case | Scenario | Status | Notes |
|---|---|---|---|
| TC1 | Happy-path conceptual | verified (1 retry) | Verifier caught real planner overreach; planner recovered |
| TC2 | Primary mechanical anchor | verification_exhausted | Retrieval coverage gap (see `failure_log.md` F1) |
| TC3 | Out-of-scope | clarification_required | Retrieval score distribution correctly signaled vague |
| TC4 | Vague input | clarification_required | Initial smoke test |
| TC5 | Multi-path mechanical | verification_exhausted | Same retrieval gap as TC2 (F2) |
| TC6 | Single-prompt ablation | completed | Baseline grounded 4/4 scenes; see `failure_log.md` F3 |

Total cost of all 6 runs: ~$0.25. Total wall-clock: ~220 seconds.

Archived run states and traces: `eval/runs_saved/phase2_evaluation/`.

## Folder guide

```
aurua/
├── README.md                               ← this file
├── AI_USAGE.md                             ← required per course policy
├── requirements.txt
├── .env.example
│
├── docs/
│   ├── phase_1_document.pdf
│   ├── phase_2_document.pdf                ← main Phase 2 submission
│   ├── architecture_diagram.pdf
│   └── phase2_section_*.md                 ← revised sections to be inserted
│
├── src/
│   ├── config.py                           ← all tunable parameters
│   ├── state.py                            ← Pydantic run-state definitions
│   ├── claude_client.py                    ← Anthropic SDK wrapper
│   ├── run.py                              ← top-level orchestrator + CLI
│   ├── agents/
│   │   ├── intent_grounding.py             ← Agent 1 (implemented)
│   │   ├── planner.py                      ← Agent 2 (implemented)
│   │   ├── verifier.py                     ← Agent 3 (implemented)
│   │   └── narration_writer.py             ← Agent 4b (Phase 3 stub)
│   ├── prompts/                            ← system prompts, versioned separately
│   └── tools/
│       └── retrieval.py                    ← FAISS + sentence-transformers
│
├── scripts/
│   ├── clean_transcript.py                 ← VTT → line-per-sentence cleaner
│   ├── apply_fixes.py                      ← auto-caption term corrections
│   └── run_tc6_baseline.py                 ← single-prompt baseline (TC6)
│
├── data/
│   ├── transcripts/                        ← 3B1B Ch3 and Ch4 transcripts
│   │   └── SOURCES.md                      ← provenance and attribution
│   └── index/                              ← cached FAISS index (gitignored)
│
├── eval/
│   ├── test_cases.csv                      ← 5 scenarios + 1 ablation
│   ├── evaluation_results.csv              ← populated from real runs
│   ├── failure_log.md                      ← 3 documented failures (F1, F2, F3)
│   ├── version_notes.md                    ← v0.2 config, v0.3 plan
│   └── runs_saved/phase2_evaluation/       ← archived run states + traces
│
├── outputs/
│   └── runs/                               ← live run outputs (gitignored)
│
└── tests/
    └── test_smoke.py                       ← 9 tests, all passing
```

## Known limitations (v0.2)

1. **Retrieval coverage gap.** FAISS + 80-word chunks missed the direct-answer span for 2 of 2 mechanical questions tested against the Ch4 transcript. Documented as failures F1 and F2 in `eval/failure_log.md`. Phase 3 will test smaller chunks, larger top-k, and query expansion.

2. **The multi-agent architecture is not yet justified by the current evaluation corpus.** The TC6 ablation (single-prompt baseline on the full transcript) outperformed the multi-agent pipeline on TC2 — same question, 1 API call vs. 7, 4/4 grounded scenes vs. 2/4. At ~1,600 words per transcript, retrieval added failure modes without buying capability that couldn't be had by fitting the whole source in context. The architecture is designed for a regime (corpora too large to fit in context) that the current evaluation does not stress. Honest writeup in `docs/phase_2_document.pdf` §5.4.

3. **Rendering branch is not wired.** Agent 4a (Animation Coder) has a prompt but no agent module calls it. Agent 4b (Narration Writer) has a stub module but is not invoked by the orchestrator. The Renderer is unimplemented. All Phase 3 work.

4. **No cross-session memory.** Each run is independent by design (see Phase 2 doc §4.2). Not a bug.

## Contact

Jorge Urias · 94815 Agentic Technologies · CMU Heinz College