# Aurua

An agentic system that turns a confusing educational passage plus a student's question into a short animated explainer video. Course project for 94815 Agentic Technologies, CMU Heinz College.

**Team:** Jorge Urias (individual project)
**Track:** Track A — Technical Build
**Status (Phase 3, v0.3):** End-to-end pipeline working. Agents 1, 2, 3, and 4a are implemented; the deterministic Renderer (Manim + ffmpeg) is wired. The canonical demo run produces a 1m22s rendered silent video for TC1. 12 evaluation runs total across two architecture versions. Agent 4b (Narration Writer) and audio muxing are reserved for v0.4.

## What it does

Given a source transcript and a student question, the pipeline:

1. Embeds the transcript once into a FAISS index (cached).
2. Generates 3 paraphrased query variants (v0.3) and retrieves relevant source spans against all of them, deduplicating by span ID.
3. Classifies the confusion as `mechanical`, `conceptual`, or `vague`. Vague classification short-circuits the pipeline with a clarifying question.
4. Plans a scene-by-scene explainer (~60–90 seconds) with per-scene grounding references.
5. Verifies each scene's claim against its cited source span using a second LLM with a distinct system prompt.
6. If any scene fails verification, revises only the flagged scenes and re-verifies. Up to 2 retries.
7. **(Phase 3)** On verified plans, generates Manim Python code per scene, renders each scene to MP4 via the `manim` CLI, then concatenates with `ffmpeg` to a single silent video.

The verifier retry loop is the piece that makes this genuinely agentic rather than a prompt chain. The rendering branch is conditional on verification — exhausted or vague-input runs stop earlier and produce structured-state evidence files, not videos.

## Architecture

```
User question + source content
        ↓
[Agent 1] Intent & Grounding   ── retrieval tool (FAISS + sentence-transformers + query expansion)
        ↓
        ├─(vague)─► clarify → stop
        ↓
[Agent 2] Explanation Planner  ←─── (revise with feedback, max 2 retries)
        ↓                            ↑
[Agent 3] Grounding Verifier  ──────┘
        ↓ (verified)
[Agent 4a] Animation Coder (Manim code per scene)
        ↓
[Renderer tool] manim subprocess (per-scene MP4) → ffmpeg concat
        ↓
Silent explainer video (.mp4)
```

Full architecture discussion including role justifications, coordination logic, and orchestration framework choice (custom Python vs. LangGraph) is in `docs/PHASE_3.md` §3 and `docs/architecture_diagram.pdf`.

## Setup

Requirements: Python 3.11+, an Anthropic API key, and a working Manim install.

```bash
cd aurua
python -m venv .venv
source .venv/bin/activate        # macOS/Linux; .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env             # edit .env and add your ANTHROPIC_API_KEY
```

**Manim system dependencies (one-time setup).** Phase 3 added Manim as a runtime dependency. On macOS:

```bash
brew install pkg-config cairo pango ffmpeg
```

LaTeX is **not** required. The Animation Coder's system prompt explicitly forbids `MathTex` and `Tex`; equations are written as `Text("∂C/∂w")` using Unicode glyphs. This trades typographic polish for a simpler install. Verify with the smoke test:

```bash
manim -ql scripts/test_manim.py HelloWorld
```

If you get an MP4 in `media/videos/test_manim/`, the install is good.

Transcripts are populated in `data/transcripts/` — see `data/transcripts/SOURCES.md` for provenance.

On first run, the retriever builds a FAISS index (~10 seconds) and caches it in `data/index/`. Delete that directory to force a rebuild if you change transcripts or retrieval parameters.

## Running the pipeline

Multi-agent pipeline with rendering (primary, produces video on verified runs):

```bash
python -m src.run \
  --question "What does the gradient of the cost function tell us about which weights to change?" \
  --source data/transcripts/3b1b_ch3.txt
```

Single-prompt baseline (TC6 ablation, no retrieval, no verifier, no rendering):

```bash
python scripts/run_tc6_baseline.py \
  --question "..." \
  --source data/transcripts/3b1b_ch4.txt
```

Output:

- Console: final plan (or clarification question), cost/latency metrics, render progress, and final video path on successful runs.
- `outputs/runs/{run_id}/state.json`: full run state.
- `outputs/runs/{run_id}/scenes/`: generated Manim Python files (one per scene).
- `outputs/runs/{run_id}/videos/`: per-scene rendered MP4s.
- `outputs/runs/{run_id}/final_silent.mp4`: concatenated final video (verified runs only).
- `eval/traces/{run_id}/`: per-call prompt/response traces, one file per agent call.

## Evaluation

12 evaluation runs total — 6 from Phase 2 (v0.2) and 6 from Phase 3 (v0.3). Results are in `eval/evaluation_results.csv`; failure analysis is in `eval/FAILURE_LOG.md`; configuration and version tracking are in `eval/VERSION_NOTES.md`; test definitions are in `eval/test_cases.csv`.

Headline results across versions:

| Case | Scenario | v0.2 result | v0.3 result | Notes |
|---|---|---|---|---|
| TC1 | Happy-path conceptual | verified (1 retry) | verified first try + verified after 1 retry on a separate run | Phase 3 canonical demo: full rendered video |
| TC2 | Primary mechanical anchor | exhausted (F1) | exhausted (F4) | Retrieval improved 4/4 spans; verifier still rejects on different grounds |
| TC3 | Out-of-scope | clarification_required | (corpus-independent) | Retrieval score distribution correctly signaled vague |
| TC4 | Vague input | clarification_required | (corpus-independent) | Verifier never invoked; correct refusal |
| TC5 | Multi-path mechanical | exhausted (F2) | exhausted (F5) | Retrieval improved; chunk truncation surfaced as new finding |
| TC6 | Single-prompt ablation | grounded 4/4 scenes | identical 4/4 scenes (reproducibility check) | Run 2 added per Phase 2 grader feedback |

**Canonical Phase 3 demo:** TC1 v0.3 full pipeline, run `170daccbae47`. 4 scenes, verifier passed after 1 retry, 4 Manim renders, concatenated to a 1m22s silent video. Total cost $0.50, total wall-clock ~3.5 minutes. Archived at `eval/runs_saved/phase3_evaluation/TC1_v3_FULL_RENDERED/`.

Total cost of all 12 runs: under $1.50. No run exceeded 10 API calls or $0.50, including full-rendering runs.

Archived run states and traces:

- `eval/runs_saved/phase2_evaluation/` — all 6 Phase 2 runs
- `eval/runs_saved/phase3_evaluation/` — all 6 Phase 3 runs

## Documented failures (F1–F5)

5 failure cases across two versions, more than the rubric's ≥2 requirement. Full writeup in `eval/FAILURE_LOG.md`.

| ID | Version | Severity | Status | Resolution |
|---|---|---|---|---|
| F1 | v0.2 | High | Partially closed in v0.3 | Retrieval improved; deeper finding (F4) emerged |
| F2 | v0.2 | Medium-high | Partially closed in v0.3 | Retrieval improved; deeper finding (F5) emerged |
| F3 | v0.2 | n/a (architectural finding) | Documented; reproduced in v0.3 | Architectural scope statement |
| F4 | v0.3 | Medium | Documented | Regime-of-applicability statement; v0.4 source-augmentation planned |
| F5 | v0.3 | Medium | Documented | v0.4 sentence-boundary chunking planned |

F1/F2 → F4/F5 form a complete fix-and-retest cycle: identify failure → propose specific fix → run it → document what improved and what new issues surfaced. F3 is the TC6 ablation finding — the single-prompt baseline outperforms the multi-agent pipeline on this corpus size, honestly documented rather than spun.

## Folder guide

```
aurua/
├── README.md                               ← this file
├── AI_USAGE.md                             ← required per course policy
├── requirements.txt
├── .env.example
│
├── docs/
│   ├── PHASE_2.md                          ← Phase 2 document
│   ├── PHASE_3.md                          ← Phase 3 document (comprehensive)
│   ├── final_report.pdf                    ← polished final report
│   ├── architecture_diagram.pdf            ← updated for Phase 3 (rendering branch added)
│   └── screenshots/
│       ├── screenshot_index.md
│       └── 01_*.png … 08_*.png
│
├── src/
│   ├── config.py                           ← all tunable parameters (v0.3 retrieval values)
│   ├── state.py                            ← Pydantic run-state definitions
│   ├── claude_client.py                    ← Anthropic SDK wrapper (handles Opus 4.7 temp deprecation)
│   ├── run.py                              ← top-level orchestrator + CLI (rendering branch wired)
│   ├── agents/
│   │   ├── intent_grounding.py             ← Agent 1 (with v0.3 query expansion)
│   │   ├── planner.py                      ← Agent 2
│   │   ├── verifier.py                     ← Agent 3
│   │   ├── animation_coder.py              ← Agent 4a (Phase 3, Opus 4.7)
│   │   └── narration_writer.py             ← Agent 4b (scaffolded; v0.4)
│   ├── prompts/                            ← system prompts, versioned separately
│   └── tools/
│       ├── retrieval.py                    ← FAISS + sentence-transformers + query expansion
│       └── renderer.py                     ← Phase 3: manim subprocess + ffmpeg concat
│
├── scripts/
│   ├── clean_transcript.py                 ← VTT → line-per-sentence cleaner
│   ├── apply_fixes.py                      ← auto-caption term corrections
│   ├── run_tc6_baseline.py                 ← single-prompt baseline (TC6)
│   └── test_manim.py                       ← smoke test for Manim install
│
├── data/
│   ├── transcripts/                        ← 3B1B Ch3 and Ch4 transcripts
│   │   └── SOURCES.md                      ← provenance and attribution
│   └── index/                              ← cached FAISS index (gitignored)
│
├── eval/
│   ├── test_cases.csv                      ← 5 scenarios + 1 ablation
│   ├── evaluation_results.csv              ← all 12 runs (Phase 2 + Phase 3)
│   ├── FAILURE_LOG.md                      ← 5 documented failures (F1–F5)
│   ├── VERSION_NOTES.md                    ← v0.2 config, v0.3 changes, v0.4 plan
│   ├── runs_saved/
│   │   ├── phase2_evaluation/              ← 6 archived runs
│   │   └── phase3_evaluation/              ← 6 archived runs (incl. TC1_v3_FULL_RENDERED)
│   └── traces/                             ← per-call prompt/response traces
│
├── outputs/
│   └── runs/                               ← live run outputs (gitignored)
│
├── media/
│   └── demo_video_link.txt                 ← 5-minute walkthrough video link
│
├── phase_submissions/
│   ├── phase1/
│   ├── phase2/
│   └── phase3/
│
└── tests/
    └── test_smoke.py                       ← 9 tests, all passing
```

## Known limitations (v0.3)

1. **TC2 and TC5 still exhaust verifier — for new reasons.** The v0.3 retrieval improvements (smaller chunks, higher top-k, query expansion) measurably improved coverage (4/4 of Intent agent's chosen spans now in top-10 vs. 0/4 in v0.2), but TC2 and TC5 still exhaust at the verifier. F4 surfaced because the source transcript is informal (Grant Sanderson never writes the chain rule as a formal product); F5 surfaced because 40-word chunks more often end mid-sentence. Both findings have specific v0.4 fixes in `eval/VERSION_NOTES.md`.

2. **Architecture not earning its keep on this corpus size.** TC6 ablation reproduced cleanly in v0.3 — the single-prompt baseline still outperforms the multi-agent pipeline on the primary anchor question. At ~1,600 words per transcript, retrieval is over-engineered. The architecture is designed for corpora that exceed context windows, which the current evaluation has not reached. Honest writeup in `docs/PHASE_3.md` §7.3.

3. **No audio in rendered videos.** Phase 3 produces silent Manim renders concatenated with ffmpeg. Agent 4b (Narration Writer) is scaffolded but not wired; TTS and audio muxing are reserved for v0.4. The grader's stated minimum was "even if TTS and ffmpeg muxing are not complete" — this iteration meets that bar with full silent video.

4. **No per-scene citation overlays in rendered video.** The Phase 2 grader noted the disclaimer scene and per-scene citations were planned but not implemented. They remain unimplemented in v0.3 — both are reserved for v0.4.

5. **Per-agent read access on `RunState` is convention-enforced, not mechanism-enforced.** Each agent's function signature documents what it reads; the orchestrator's call order respects dependencies. v0.4 adds typed views per agent (`RunStateForVerifier`, etc.). Documented in `docs/PHASE_3.md` §4.2.

6. **Preference test was not executed.** The Phase 2 evaluation plan called for blind comparison with 5 reviewers on TC1, TC2, TC5 outputs. Time-constrained; deferred to v0.4.

7. **No cross-session memory.** Each run is independent by design (see PHASE_3.md §4). Not a bug.

## v0.4 priority list

Documented in `eval/VERSION_NOTES.md`. In priority order:

1. Sentence-boundary chunking (addresses F5)
2. Source augmentation with formal-derivation source (addresses F4)
3. Wire Agent 4b (Narration Writer) + OpenAI TTS + ffmpeg muxing
4. Per-agent typed views on `RunState`
5. Per-scene citation overlay in rendered video
6. Disclaimer scene at start of each rendered video
7. Larger-corpus stress test (addresses F3 defense)
8. Preference test execution

## Contact

Jorge Urias · 94815 Agentic Technologies · CMU Heinz College