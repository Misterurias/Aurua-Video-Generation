# Aurua Version Notes

This file tracks the configuration used for each evaluation run so results can be reproduced and changes between Phase 2 and Phase 3 can be traced.

---

## v0.2 — Phase 2 evaluation run (2026-04-16)

All 6 test cases in `eval/test_cases.csv` were executed under this version.

### Models

- **Intent agent (Agent 1):** `claude-sonnet-4-6`, temperature 0.0
- **Planner (Agent 2):** `claude-sonnet-4-6`, temperature 0.0
- **Verifier (Agent 3):** `claude-sonnet-4-6`, temperature 0.0 (same model as Planner; distinct system prompt)
- **TC6 single-prompt baseline:** `claude-sonnet-4-6`, temperature 0.0

Models specified in `.env` via `AURUA_AGENT_MODEL` and `AURUA_VERIFIER_MODEL`. Coder model (`AURUA_CODER_MODEL=claude-opus-4-7`) is set but unused in Phase 2 because the rendering branch is not wired.

### Retrieval configuration

- **Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` (384-dim, normalized)
- **Chunk size:** 80 words
- **Chunk overlap:** 20 words
- **FAISS index:** `IndexFlatIP` (exact cosine similarity via inner product on normalized vectors)
- **Top-k:** 5

### Pipeline control

- **Max verifier retries:** 2 (so up to 3 planner+verifier cycles per run)
- **Max tokens per call:** 4096

### Source corpus

- `data/transcripts/3b1b_ch3.txt` — 185 lines, ~2,223 words (3B1B "Backpropagation, intuitively")
- `data/transcripts/3b1b_ch4.txt` — 130 lines, ~1,623 words (3B1B "Backpropagation calculus")

Transcripts obtained via `yt-dlp --write-sub --sub-langs en` on 2026-04-16, cleaned with `scripts/clean_transcript.py` and `scripts/apply_fixes.py`. Sources are human-reviewed English captions, not auto-generated.

### Test cases executed

| case | run_id | status | notes |
|---|---|---|---|
| TC1 | 6c434c14903b | verified (1 retry) | Verifier caught real planner overreach; planner recovered |
| TC2 | 6bfe71e485a1 | verification_exhausted | See failure_log.md F1 |
| TC3 | 51ce64b5427c | clarification_required | Retrieval score signal worked |
| TC4 | 2c45d37fb4d3 | clarification_required | Initial smoke test |
| TC5 | 84834de8a198 | verification_exhausted | See failure_log.md F2 |
| TC6 | tc6_ddbcd2db | completed (baseline) | See failure_log.md F3 |

Total API cost across all 6 runs: approximately $0.25. Total wall-clock: ~220 seconds.

### Known issues in v0.2

1. **Retrieval coverage gap** (failures F1, F2): FAISS + 80-word chunks missed the direct-answer span for 2 of 2 mechanical questions on Ch4. Documented in `failure_log.md`.
2. **Single-prompt baseline outperformed pipeline on TC6** (failure F3): A single Claude call with full transcript in context produced better-grounded output than the multi-agent pipeline on the same question. The current corpus is small enough that retrieval is over-engineered. Documented.
3. **Verifier over-scoping** (observed during TC1 and TC2): On some retries, the verifier rejected scenes for reasons tied to visual_goal detail rather than the claim itself — e.g., *"the span does not show the derivative operation or mention the bias term being crossed out"* when the claim text was actually supported. Not logged as a separate failure because retrievability fixed it in TC1 and the underlying coverage gap masked it in TC2.
4. **Intent misclassification on TC5**: Question was expected to be labeled `mechanical` but was classified `conceptual`. The question does have a conceptual framing ("why does the chain rule give us a sum..."), so this is borderline. Not logged as a failure.

### Files archived

All run states and traces archived to `eval/runs_saved/phase2_evaluation/`:

```
eval/runs_saved/phase2_evaluation/
├── TC1_verified_retry1/
├── TC2_exhausted/
├── TC3_vague/
├── TC4_vague/
├── TC5_exhausted_multi_path/
└── TC6_single_prompt_baseline/
```

---

## v0.3 — planned for Phase 3

Changes planned between v0.2 and v0.3:

1. **Retrieval fix** (addresses F1/F2): Reduce chunk size from 80 to 40 words, raise top-k from 5 to 10, add optional query-expansion step in Agent 1. Regenerate FAISS index.
2. **Ablation stress test** (addresses F3): Add a test case using a combined, larger-than-context corpus to demonstrate the regime where the multi-agent architecture genuinely outperforms the single-prompt baseline.
3. **Rendering branch** (Phase 3 deliverable): Wire Agent 4a (Animation Coder) and Agent 4b (Narration Writer), plus the deterministic Renderer (Manim + TTS + ffmpeg), for scenario 2 (TC2 primary anchor) at minimum.
4. **Verifier prompt tuning** (addresses verifier over-scoping observation): Clarify that verifier should judge the `claim` field, not the `visual_goal` field. Visual goals are plans for animation, not grounding claims.

Each change will be noted here with its run_id once tested.

## v0.3 — Phase 3 retrieval fixes + rendering branch (April 28, 2026)
 
### Changes from v0.2
 
**Retrieval fixes (addressing F1/F2):**
1. **`CHUNK_SIZE_WORDS`: 80 → 40.** Smaller chunks have more focused semantic vectors; a chunk containing one specific claim is no longer diluted by 79 surrounding words.
2. **`CHUNK_OVERLAP_WORDS`: 20 → 15.** Proportional reduction to maintain overlap fraction.
3. **`TOP_K_RETRIEVAL`: 5 → 10.** Retrieves more candidates so the right span has a wider margin to clear retrieval. The Planner can ignore noise; what it can't do is ground claims in a span it never saw.
4. **Query expansion (NEW).** Before embedding the user's question for FAISS, Agent 1 calls Claude (one extra API call) to generate 3 paraphrased variants. All 4 queries hit the index; results are deduplicated by span_id and ranked by max score across queries. This addresses the case where the answer span uses different vocabulary than the question.
**Rendering branch (NEW):**
5. **Animation Coder (Agent 4a) wired.** `claude-opus-4-7` (no temperature parameter — the model deprecated it; we send the default and skip the param). Generates Manim Community Edition code per scene as raw text. Sequential single Claude call per scene. Output written to `outputs/runs/<run_id>/scenes/scene_NN.py`.
6. **Renderer wired (deterministic tool, not an agent).** Subprocess calls to `manim` CLI for per-scene rendering, `ffmpeg` for concatenation. No LLM. Output: `outputs/runs/<run_id>/videos/scene_NN.mp4` and `outputs/runs/<run_id>/final_silent.mp4`.
 
### Why these specific changes
The v0.2 failure analysis (`failure_log.md` F1 and F2) named retrieval coverage as the root cause. The three retrieval knobs are the standard levers for retrieval coverage:
- Smaller chunks → tighter embeddings (precision)
- Higher top-k → wider candidate set (recall)
- Query expansion → handles vocabulary mismatch between question and source
The Phase 2 grader explicitly named these as "specific and testable" fixes and called for v0.3 results in Phase 3.
 
The rendering branch addresses Phase 2 grader's first ask: produce at least one rendered video to satisfy the final-artifact requirement.
 
### Other config (unchanged from v0.2)
- Same models for Agents 1–3
- Same temperatures for Sonnet (0.0); Opus 4.7 has no temperature parameter
- Same retry budget (2)
- Same FAISS index type (`IndexFlatIP`)
- Same embedding model
### Runs executed (v0.3)
 
| Test case | Run ID | Status | Cost | vs v0.2 | Notes |
|---|---|---|---|---|---|
| TC2 | `c3061f8c2527` | exhausted | $0.10 | -$0.02 | F1 partially closed; F4 emerged |
| TC1 (first try) | `fa3f9a2a4f8d` | verified | $0.07 | -$0.02 | First-try pass; v0.2 needed retry |
| TC1 (subtle correction) | `97fb7e6b6768` | verified (retry 1) | $0.08 | n/a | Different rejection trace; verifier caught subtler drift |
| **TC1 (full pipeline)** | **`170daccbae47`** | **rendered** | **$0.50** | n/a | **Canonical demo; 1m22s silent video** |
| TC5 | `d922193d24df` | exhausted | $0.10 | -$0.02 | F2 partially closed; F5 emerged |
| TC6 (run 2) | `tc6_2c72dedd` | n/a (baseline) | $0.04 | n/a | Methodology fix; F3 reproduced exactly |
 
### v0.3 architectural findings
 
**F1 (TC2 — primary anchor) — PARTIALLY CLOSED.**
 
In v0.2, the Intent agent's chosen 4 relevant spans were *all* missed by retrieval (rank 6+ or absent). In v0.3, *all 4* of those spans now appear in the top-10. Retrieval coverage measurably improved.
 
However, TC2 still exhausted — for a different reason. The verifier's complaint shifted: in v0.2 the rejected scenes cited spans that were *on the wrong topic* (dz/da rather than dz/dw). In v0.3 the cited spans are topically correct but *don't contain the formal chain-rule decomposition*. The transcript is informal — Grant Sanderson never writes the chain rule out as a formal product; he gestures at it ("looks essentially the same"). The Planner trying to formalize an informal source will always fail strict grounding.
 
This is a *deeper* finding than F1, documented as F4.
 
**F2 (TC5 — multi-path) — PARTIALLY CLOSED.**
 
In v0.2, retrieval missed L115-119 (the multi-path explanation) entirely. In v0.3, retrieval surfaces the chain-rule territory (L108-111, L82-85) but L115-119 itself is still not in the top-10.
 
But the verifier's complaint reveals a *new* issue specific to v0.3: with chunk size reduced from 80 → 40 words, more chunks now end mid-sentence. The verifier's rejection on attempt 2 reads: *"the sentence is cut off and does not actually contain the full claim."* Smaller chunks introduced sentence-truncation artifacts that strip the key payload from the cited span.
 
This is also a *deeper* finding, documented as F5.
 
**F3 (single-prompt baseline) — REPRODUCED.**
 
Run 2 of TC6 produced a functionally identical 4-scene plan with identical line citations (L31-33, L52-53, L63, L66-68). The baseline result is stable, not a fluke. The architectural concession from v0.2 stands.
 
**Trade-off summary:**
 
| | v0.2 | v0.3 |
|---|---|---|
| TC1 (happy path) | verified after 1 retry | verified first try (improvement) |
| TC2 (primary anchor) | exhausted (F1: wrong-topic spans) | exhausted (F4: source informality) |
| TC5 (multi-path) | exhausted (F2: missed answer span) | exhausted (F5: chunk truncation) |
| Retrieval scores | top ceiling 0.68 | top ceiling 0.72 |
| Cost per run | ~$0.085-0.121 | ~$0.07-0.10 |
 
v0.3 made retrieval measurably better (more relevant spans, higher scores, lower cost). It also made TC1's happy path cleaner. But the failure modes on TC2 and TC5 *transformed* rather than *resolved* — better retrieval exposed deeper limitations in the source material and chunking strategy.
 
### Reproducibility
- Temperature 0.0 on Sonnet 4.6 is deterministic across calls
- Opus 4.7 has no temperature parameter; outputs sampled but stable across runs in our experience (TC6 run-2 confirms this empirically — same input, same model, identical 4-scene plan with identical citations)
- FAISS index is rebuilt from scratch on `rm -rf data/index/`
- All runs serialized to `outputs/runs/<run_id>/state.json`
- Manim renders are deterministic for a given input file
---
 
## What's NOT changed in v0.3
- Agent 1, 2, or 3 prompts — the retrieval fix was isolated to the retrieval layer and Agent 1's pre-retrieval query expansion step
- Verifier strictness — strictness IS the verifier's value proposition; loosening it to make TC2 pass would be a fudge
- Source transcripts
- Test cases
- Coordination logic (custom orchestrator in `src/run.py`)
## What's planned for v0.4 (post-presentation)
- Address F4 by augmenting source with formal-derivation material (textbook chapter alongside transcript)
- Address F5 by sentence-boundary-aware chunking (chunks end on `. ! ?`, not at fixed word counts)
- Wire Agent 4b (Narration Writer) and OpenAI TTS for audio
- ffmpeg muxing for narrated final video
- Per-agent read access boundaries on RunState (per Phase 2 grader feedback)