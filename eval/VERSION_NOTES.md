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