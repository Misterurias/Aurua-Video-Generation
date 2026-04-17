# Aurua Failure Log

This log documents concrete failure cases observed during Phase 2 evaluation, their root causes, and the fixes planned for Phase 3. All evidence is drawn from the run traces archived in `eval/runs_saved/phase2_evaluation/` and the full state JSONs in `outputs/runs/`.

Rubric alignment: Phase 3 requires "at least two failure cases" with "what changed after testing." This log documents three failures (two instances of the same root cause, one architectural finding) observed under v0.2 of the system.

---

## Failure 1 — Retrieval coverage gap (TC2)

**failure_id:** F1
**date:** 2026-04-16
**version_tested:** v0.2 (Agents 1–3, MiniLM embeddings, 80-word chunks, top-k=5)
**severity:** High — blocks primary anchor test case
**current_status:** Documented; fix planned for Phase 3 (not yet implemented)

### What triggered the problem

Test case TC2 asks: *"Why is the derivative of the cost with respect to a weight proportional to the activation feeding into it?"* This question has a direct, unambiguous answer in the source transcript at `3b1b_ch4.txt:L63`:

> *"And the derivative of z(L) with respect to w(L)... In this case comes out to be a(L-1)."*

### What happened

FAISS retrieval did not surface the L63 span in its top-5 results. The retrieved spans covered adjacent material (the chain rule framing, the goal of finding `dC/dw`, the derivative of `z` with respect to `a(L-1)` — the *reverse* derivative) but not the specific claim `dz/dw = a(L-1)`.

The Planner tried to construct a plan anyway. Its scene 2 originally claimed *"dz(L)/dw(L) = a(L-1)"* — a true statement — but cited span `0c04087f7a` (lines 83-89), which actually discusses `dz/da(L-1) = w(L)`, a different derivative.

The Verifier caught this precisely: *"The span states that the sensitivity of z to the previous activation a(L-1) is w(L) (i.e., dz/da(L-1) = w(L)), not that dz/dw(L) = a(L-1). The claim reverses which derivative equals which quantity."*

Across three verify/revise cycles the Planner attempted increasingly careful rephrasings, but because no retrieved span *actually contained* the target fact, no revision could succeed. The pipeline correctly exhausted its retry budget and returned `verification_exhausted` after 7 API calls.

### Root cause

The 80-word sliding window chunked the transcript such that L63 landed in a chunk whose embedding was not close enough to the query "derivative of cost proportional to activation" to make FAISS's top-5. The planner was forced to work from neighboring material; the verifier correctly refused to approve claims whose cited spans did not support them.

This is a retrieval-layer failure, not a planner or verifier failure. Both downstream agents behaved as designed.

### Fix attempted

None in Phase 2. The failure was documented rather than fixed, to preserve the "before" state for the Phase 3 iteration narrative.

### Fix planned for Phase 3

Three changes to test, in order of lowest cost first:

1. **Increase top-k from 5 to 10.** Larger span budget, more chance of including the answer.
2. **Reduce chunk size from 80 to 40 words.** Finer-grained chunks mean less chance of key facts being buried in context. Regenerate the FAISS index.
3. **Add query expansion in Agent 1.** Before retrieval, have the Intent agent propose 2–3 alternative phrasings of the question to broaden semantic coverage.

### Evidence

- `eval/runs_saved/phase2_evaluation/TC2_exhausted/traces/03_verifier_attempt_0.txt` — first rejection
- `eval/runs_saved/phase2_evaluation/TC2_exhausted/traces/03_verifier_attempt_2.txt` — third (final) rejection
- `eval/runs_saved/phase2_evaluation/TC2_exhausted/state.json` — full state

---

## Failure 2 — Same retrieval coverage gap recurs (TC5)

**failure_id:** F2
**date:** 2026-04-16
**version_tested:** v0.2
**severity:** High — confirms F1 is a pattern
**current_status:** Same root cause as F1; same fix planned

### What triggered the problem

Test case TC5 asks: *"Why does the chain rule give us a sum over paths when a neuron connects to multiple neurons?"* The answer is at `3b1b_ch4.txt:L115-L119`:

> *"the neuron influences the cost function through multiple different paths. That is, on the one hand, it influences a(L)0, which plays a role in the cost function, but it also has an influence on a(L)1, which also plays a role in the cost function, and you have to add those up."*

### What happened

Retrieval's top-5 did not include the L115-119 span. By verify/revise cycle 2 the verifier had passed scenes 1, 2, and 4, but scene 3 — the one containing the core sum-over-paths claim — never grounded because no retrieved span supported it. Run exhausted after 7 API calls.

### Why this matters more than F1 alone

The two failures together show that F1 is not an isolated incident. FAISS + MiniLM-L6-v2 + 80-word chunks missed the direct-answer span in **2 of 2** mechanical-question cases tested against Ch4. This is a reliable reproduction of the coverage gap, not bad luck.

### Evidence

- `eval/runs_saved/phase2_evaluation/TC5_exhausted_multi_path/traces/03_verifier_attempt_2.txt`
- `eval/runs_saved/phase2_evaluation/TC5_exhausted_multi_path/state.json`

---

## Failure 3 — Architectural finding: baseline outperforms pipeline on small corpus (TC6)

**failure_id:** F3
**date:** 2026-04-16
**version_tested:** v0.2 vs. single-prompt baseline
**severity:** Medium — reveals a regime where the architecture does not yet earn its complexity
**current_status:** Open architectural question; not a bug but a finding worth documenting

### What triggered the problem

TC6 re-ran TC2's question through a single-prompt baseline (`scripts/run_tc6_baseline.py`): one Claude call with the full transcript in context, no retrieval, no verifier, no loop.

### What happened

The baseline produced a clean 4-scene plan in a single API call, 17 seconds, ~$0.04. All four cited quotes are verbatim from the transcript. All four line locations are accurate. Scene 3 cites line 63 — the exact span that the multi-agent pipeline's retrieval failed to surface in TC2.

### Why this is a failure (not of the baseline, of the argument)

The Phase 1 and initial Phase 2 documentation argued that the multi-agent architecture earns its complexity by preventing grounding hallucinations. On TC6 specifically, this argument is not supported by the data:

- Multi-agent (TC2): 7 calls, `verification_exhausted`, 2 of 4 final scenes ungrounded
- Single-prompt (TC6): 1 call, clean output, 4 of 4 scenes correctly grounded

At a corpus size of ~1,600 words, putting the whole transcript in context is clearly tractable and produces better results than retrieval-based chunking.

### Honest interpretation

Two things are true simultaneously:

1. **The verifier itself is valuable.** TC1 showed the verifier catching a genuine planner overreach ("each partial derivative measures how sensitively the cost responds to a small change") where the cited span didn't actually say that, and the planner successfully revised. That is the architecture working as designed.

2. **Retrieval is not currently earning its cost on this corpus.** With ~1,600 words of transcript, FAISS over-engineered the problem: it ran correctly but removed context the planner needed to succeed.

The multi-agent architecture pays off in regimes where the corpus cannot fit in context (full textbooks, multi-hour lecture series) and where verification catches drift that single-prompt baselines don't reveal because there's no second opinion. Neither condition is stressed in the current Phase 2 evaluation.

### What this means for Phase 3

Two changes, in order:

1. **Fix retrieval coverage** (F1/F2 fix). Smaller chunks, larger top-k, query expansion. Re-run TC2 and TC6 — if the pipeline then matches the baseline, the architecture is justified within the current corpus. If not, we have deeper concerns to document.

2. **Stress-test the architecture in the regime it's designed for.** Add a test case against a larger source (multiple combined transcripts, or a textbook chapter) where the baseline's "fit everything in context" approach breaks down. This is the scaling argument the current evaluation doesn't cover.

Phase 2 §5.4 of the project report has been updated to reflect these findings honestly rather than claiming the architecture outperformed the baseline on all cases.

### Evidence

- `eval/runs_saved/phase2_evaluation/TC6_single_prompt_baseline/state.json` — full baseline output including verbatim quotes and line locations
- `docs/phase_2_document.pdf` §5.4 (revised) — updated comparative analysis

---

## Summary table

| ID | Severity | Trigger | Root cause | Fix planned |
|----|---|---|---|---|
| F1 | High | TC2 question | Retrieval missed answer span | Chunk size ↓, top-k ↑, query expansion |
| F2 | High | TC5 question | Same as F1 | Same as F1 |
| F3 | Medium | TC6 ablation | Architecture not earning complexity on small corpus | Fix F1/F2, then stress-test on larger corpus |

F1 and F2 are two instances of one underlying fault. F3 is an architectural finding, not a bug. Total: **three documented failures covering two distinct findings** — meeting the rubric's requirement of "at least two failure cases" while also doing honest self-critique.