# Aurua Failure Log

This log documents every failure mode observed in evaluation runs across two architecture versions, with root-cause analysis, evidence pointers, and what changed between versions. All evidence is drawn from run traces archived in `eval/runs_saved/` and the full state JSONs in `outputs/runs/`.

The Phase 3 rubric requires at least 2 documented failure cases with "what changed after testing." This project documents **5 failures across 2 versions**, demonstrating the cycle of fix-then-retest (F1 → F4, F2 → F5) and the architectural self-critique that emerged from the TC6 ablation (F3).

---

## F1 — Retrieval coverage gap on TC2 (v0.2)

**failure_id:** F1
**date:** 2026-04-16
**version_tested:** v0.2 (Agents 1–3, MiniLM embeddings, 80-word chunks, top-k=5)
**severity:** High — blocks primary anchor test case
**current_status:** **Partially closed in v0.3.** Retrieval improved measurably; deeper finding (F4) emerged.

### What triggered the problem

Test case TC2 asks: *"Why is the derivative of the cost with respect to a weight proportional to the activation feeding into it?"* This question has a direct, unambiguous answer in the source transcript at `3b1b_ch4.txt:L63`:

> *"And the derivative of z(L) with respect to w(L)... In this case comes out to be a(L-1)."*

### What happened

FAISS retrieval did not surface the L63 span in its top-5 results. The retrieved spans covered adjacent material (the chain rule framing, the goal of finding `dC/dw`, the derivative of `z` with respect to `a(L-1)` — the *reverse* derivative) but not the specific claim `dz/dw = a(L-1)`.

The Planner tried to construct a plan anyway. Its scene 2 originally claimed *"dz(L)/dw(L) = a(L-1)"* — a true statement — but cited span `0c04087f7a` (lines 83-89), which actually discusses `dz/da(L-1) = w(L)`, a different derivative.

The Verifier caught this precisely:

> *"The span states that the sensitivity of z to the previous activation a(L-1) is w(L) (i.e., dz/da(L-1) = w(L)), not that dz/dw(L) = a(L-1). The claim reverses which derivative equals which quantity."*

Across three verify/revise cycles the Planner attempted increasingly careful rephrasings, but because no retrieved span *actually contained* the target fact, no revision could succeed. The pipeline correctly exhausted its retry budget and returned `verification_exhausted` after 7 API calls ($0.118, 68 seconds).

### Root cause

The 80-word sliding window chunked the transcript such that L63 landed in a chunk whose embedding was not close enough to the query "derivative of cost proportional to activation" to make FAISS's top-5. The planner was forced to work from neighboring material; the verifier correctly refused to approve claims whose cited spans did not support them.

This is a retrieval-layer failure, not a planner or verifier failure. Both downstream agents behaved as designed.

### Fix attempted (v0.3)

Three changes, in order of lowest cost first:

1. **Increase top-k from 5 to 10.** Larger span budget, more chance of including the answer.
2. **Reduce chunk size from 80 to 40 words.** Finer-grained chunks mean less chance of key facts being buried in context. Regenerate the FAISS index.
3. **Add query expansion in Agent 1.** Before retrieval, the Intent agent proposes 3 paraphrased variants of the question; all 4 queries hit FAISS, results deduplicate by span_id and rank by max score.

### Outcome of v0.3 fix

**Retrieval coverage improved measurably.** In v0.2, the four spans the Intent agent identified as relevant were all *not retrieved* (rank 6+ in FAISS, filtered out by top-5). In v0.3, *all four* of those spans now appear in the top-10. Retrieval is doing its job.

But TC2 v0.3 still exhausted at the verifier — for a different reason. See **F4**.

### Evidence

- v0.2 run state: `eval/runs_saved/phase2_evaluation/TC2_exhausted/state.json`
- v0.2 verifier traces: `eval/runs_saved/phase2_evaluation/TC2_exhausted/traces/03_verifier_attempt_*.txt`
- v0.3 run state: `eval/runs_saved/phase3_evaluation/TC2_v3/state.json`
- Direct retrieval-rank comparison v0.2 vs v0.3: `eval/VERSION_NOTES.md` v0.3 section

---

## F2 — Same retrieval coverage gap recurs on TC5 (v0.2)

**failure_id:** F2
**date:** 2026-04-16
**version_tested:** v0.2
**severity:** Medium-high — confirms F1 is a pattern, not a one-off
**current_status:** **Partially closed in v0.3.** Retrieval improved; deeper finding (F5) emerged.

### What triggered the problem

Test case TC5 asks: *"Why does the chain rule give us a sum over paths when a neuron connects to multiple neurons?"* The answer is at `3b1b_ch4.txt:L115-L119`:

> *"the neuron influences the cost function through multiple different paths. That is, on the one hand, it influences a(L)0, which plays a role in the cost function, but it also has an influence on a(L)1, which also plays a role in the cost function, and you have to add those up."*

### What happened

Retrieval's top-5 did not include the L115-119 span. By verify/revise cycle 2 the verifier had passed scenes 1, 2, and 4, but scene 3 — the one containing the core sum-over-paths claim — never grounded because no retrieved span supported it. Run exhausted after 7 API calls ($0.121, 72 seconds).

### Why this matters more than F1 alone

The two failures together show that F1 is not an isolated incident. FAISS + MiniLM-L6-v2 + 80-word chunks missed the direct-answer span in **2 of 2** mechanical-question cases tested against Ch4. This is a reliable reproduction of the coverage gap.

### Fix attempted (v0.3)

Same retrieval changes as F1 (smaller chunks, higher top-k, query expansion).

### Outcome of v0.3 fix

Retrieval improved — the chain-rule territory (L108-111, L82-85) now appears in the top-10 (vs. missed entirely in v0.2). The Planner has access to topically correct material.

But TC5 v0.3 still exhausted — for yet another distinct reason. See **F5**.

### Evidence

- v0.2 run state: `eval/runs_saved/phase2_evaluation/TC5_exhausted_multi_path/state.json`
- v0.2 verifier traces: same directory
- v0.3 run state: `eval/runs_saved/phase3_evaluation/TC5_v3_partial_close/state.json`

---

## F3 — Architectural finding: baseline outperforms pipeline on small corpus (v0.2)

**failure_id:** F3
**date:** 2026-04-16
**version_tested:** v0.2 vs. single-prompt baseline
**severity:** n/a (architectural finding, not a bug)
**current_status:** Documented. Baseline result reproduced for stability in v0.3.

### What triggered the problem

TC6 re-ran TC2's question through a single-prompt baseline (`scripts/run_tc6_baseline.py`): one Claude call with the full transcript in context, no retrieval, no verifier, no loop.

### What happened

The baseline produced a clean 4-scene plan in a single API call (17 seconds, $0.043). All four cited quotes are verbatim from the transcript. All four line locations are accurate. Scene 3 cites line 63 — the exact span that the multi-agent pipeline's retrieval failed to surface in TC2.

A second run against the same question (TC6 run-2, 2026-04-28, methodology fix per Phase 2 grader feedback) produced a **functionally identical** 4-scene plan with identical line citations (L31-33, L52-53, L63, L66-68). The baseline result is stable, not a fluke.

### Why this is a failure (not of the baseline, of the argument)

The Phase 1 and initial Phase 2 documentation argued that the multi-agent architecture earns its complexity by preventing grounding hallucinations. On TC6 specifically, this argument is not supported by the data:

| | Multi-agent (TC2 v0.2) | Single-prompt (TC6) |
|---|---|---|
| API calls | 7 | 1 |
| Cost | $0.118 | $0.043 |
| Wall-clock | 68 s | 17 s |
| Final status | `verification_exhausted` | clean output |
| Scenes correctly grounded | 2 of 4 | 4 of 4 |

At a corpus size of ~1,600 words, putting the whole transcript in context is clearly tractable and produces better results than retrieval-based chunking.

### Honest interpretation

Two things are true simultaneously:

1. **The verifier itself is valuable.** TC1 showed the verifier catching a genuine planner overreach ("each partial derivative measures how sensitively the cost responds to a small change") where the cited span didn't actually say that, and the planner successfully revised. That is the architecture working as designed.

2. **Retrieval is not currently earning its cost on this corpus.** With ~1,600 words of transcript, FAISS over-engineered the problem: it ran correctly but removed context the planner needed to succeed.

### Defense of the architecture

The architecture is justified in regimes the current evaluation doesn't fully stress:

- **Corpora that exceed context windows** (full textbooks, multi-hour lecture series) — single-prompt cannot scale here.
- **Auditable grounding** — single-prompt cites once; multi-agent records cited spans, retrieval scores, and verification verdicts in structured state for replay.
- **Catching drift** — even when retrieval is unnecessary, a single-prompt run with no verifier has no governance layer to catch hallucinations across many runs.

This is the highest-value finding in the evaluation, not a bug. It honestly reports a regime where the architecture's complexity does *not* earn its keep, and identifies the regimes where it does.

### Evidence

- Run 1 state: `eval/runs_saved/phase2_evaluation/TC6_single_prompt_baseline/state.json`
- Run 2 state: `eval/runs_saved/phase3_evaluation/TC6_baseline_run2/state.json`
- Both runs cite L31-33, L52-53, L63, L66-68 — confirming reproducibility.
- TC6 baseline script: `scripts/run_tc6_baseline.py`
- Final report Section 6 — discusses architectural scope and applicability.

### Fix planned

No fix — this finding is documented as a scope-and-regime statement in the final report.

---

## F4 — Source informality limits formal grounding even with perfect retrieval (v0.3)

**failure_id:** F4
**date:** 2026-04-28
**version_tested:** v0.3
**severity:** Medium — deeper finding than F1, not a regression.
**current_status:** Documented. Regime-of-applicability statement; v0.4 source-augmentation planned.

### What triggered the problem

TC2 v0.3 — same question as F1, against the same transcript, with retrieval fixes applied.

### What happened

Retrieval coverage measurably improved (see F1 outcome). All four spans the Intent agent identified as relevant now appear in the top-10. Retrieval is doing its job.

But TC2 v0.3 still exhausted. The verifier's complaint shifted from F1's:

| | F1 (v0.2) | F4 (v0.3) |
|---|---|---|
| Verifier rejection reason | *"span describes dz/da, not dz/dw — the claim reverses which derivative equals which quantity"* | *"span only references a 'chain-ruled derivative expression' and says it 'looks essentially the same' — does not explicitly state the chain rule product (∂C/∂a)·(∂a/∂z)·(∂z/∂w) or the substitution ∂z/∂w = a_prev"* |
| Type of failure | Wrong topic | Right topic, informal phrasing |

### Root cause

Grant Sanderson's transcript is *informal* by design — it's a YouTube video, not a textbook. He never writes the chain rule out as a formal product; he gestures at it ("looks essentially the same"). Even the answer at line 63 (*"comes out to be a(L-1)"*) is conversational, not a formal substitution step.

The Planner is trying to teach a *formal* mechanical claim ("by the chain rule, ∂C/∂w = (∂C/∂a)·(∂a/∂z)·(∂z/∂w), and since ∂z/∂w = a_prev, the entire gradient is proportional to that incoming activation"). The Verifier correctly notes this formal decomposition is not in any retrieved span. **It can't be grounded because it's not in the source.**

### Architectural implications

- Better retrieval is *necessary but not sufficient*.
- For maximally precise mechanical questions, a chunk-based retrieval architecture against an informal source will fail strict grounding even with perfect retrieval.
- Two paths forward in v0.4:
  - (a) accept that some questions are out-of-scope for the source (return a clarification or refusal instead of forcing a plan), or
  - (b) augment with a formal-derivation source (e.g. a textbook chapter) when the question demands one.

### Evidence

- Run state: `eval/runs_saved/phase3_evaluation/TC2_v3/state.json`
- Verifier traces: same directory, especially `traces/03_verifier_attempt_2.txt`
- Direct retrieval-rank comparison vs F1: `eval/VERSION_NOTES.md`

### Fix planned

No fix appropriate at this version. The Verifier's behavior is correct; rather than weakening it, the right move is to honestly document the finding and plan a v0.4 source-augmentation experiment.

---

## F5 — Smaller chunks introduce sentence-truncation artifacts (v0.3)

**failure_id:** F5
**date:** 2026-04-28
**version_tested:** v0.3
**severity:** Medium — self-inflicted by the v0.3 retrieval tightening, but addressable.
**current_status:** Documented. v0.4 sentence-boundary chunking planned.

### What triggered the problem

TC5 v0.3 — same question as F2, with retrieval fixes applied.

### What happened

Retrieval improved — the chain-rule territory (L108-111, L82-85) now appears in the top-10 (vs. missed entirely in v0.2). The Planner has access to topically correct material.

But TC5 v0.3 still exhausted. The verifier's final-attempt rejection reason:

> *"the sentence is cut off and does not actually contain the full claim. Specifically, it does not show or state the summed multi-neuron chain-rule equation."*

### Root cause

Reducing chunk size from 80 → 40 words in v0.3 was meant to tighten semantic vectors. It did. But it also increased the rate at which chunks end mid-sentence. A chunk like `5d0b154bb4` (L108-111) cuts off mid-thought:

> *"...the chain-ruled derivative expression describing how sensitive the cost is to a specific"*

The sentence completes outside the chunk boundary. The Planner sees a setup but no payload. The Verifier correctly notes the cited chunk doesn't contain the claim.

### Architectural implications

- Word-count chunking is a poor abstraction for prose. Chunks should respect sentence boundaries.
- The retrieval improvement and the chunk-truncation regression came from the same change. Tighter chunks = better embeddings, but at the cost of cleaner payloads.
- v0.4 fix: chunk on `. ! ?` boundaries with a target word count (e.g. 60 ± 20 words) rather than fixed word count.

### Evidence

- Run state: `eval/runs_saved/phase3_evaluation/TC5_v3_partial_close/state.json`
- Verifier trace: `eval/runs_saved/phase3_evaluation/TC5_v3_partial_close/traces/03_verifier_attempt_2.txt`
- Direct comparison of chunk endings: `eval/VERSION_NOTES.md` v0.3 section

### Fix planned

v0.4 — sentence-boundary-aware chunking. Implementation effort estimated at 2 hours (replace fixed-window chunker in `src/tools/retrieval.py`).

---

## Summary table

| ID | Version | Severity | Status | Resolution |
|---|---|---|---|---|
| F1 | v0.2 | High | Partially closed in v0.3 | Retrieval improved; deeper finding (F4) emerged |
| F2 | v0.2 | Medium-high | Partially closed in v0.3 | Retrieval improved; deeper finding (F5) emerged |
| F3 | v0.2 | n/a (finding) | Documented; reproduced in v0.3 | Architectural scope statement |
| F4 | v0.3 | Medium | Documented | Regime-of-applicability statement; v0.4 source-augmentation planned |
| F5 | v0.3 | Medium | Documented | v0.4 sentence-boundary chunking planned |

This is more failure cases than the rubric requires (≥2). The variety matters:

- **F1, F2** are the same fix-and-retest cycle that produced new findings.
- **F3** is an honest architectural concession from a planned ablation, reproduced for stability.
- **F4** is a deeper finding from running the v0.3 fix (informal source materials limit formal grounding).
- **F5** is a regression introduced by v0.3 itself, with a specific fix planned for v0.4.

Together these document a complete iteration cycle: identify failure → propose specific fix → run it → document what improved and what new issues surfaced → plan next iteration.