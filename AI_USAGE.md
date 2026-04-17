# AI Usage Disclosure — Aurua

This file documents every use of generative AI tools in the creation of the Aurua project, per 94815 course policy.

Each entry includes:
- Tool name and version
- Date of use
- What the tool was used for
- What was changed manually afterward
- What was independently verified

Entries are in reverse chronological order (most recent first).

---

## Entry 03 — Phase 2 evaluation analysis, failure-log drafting, and §5.4 rewrite

**Tool:** Claude Opus 4.7 (via claude.ai web interface)
**Date:** 2026-04-16
**Used for:**
- Analyzing the full set of Phase 2 evaluation runs (TC1, TC2, TC3, TC4, TC5, TC6), including reading every trace file and state.json and identifying patterns across failures.
- Drafting `eval/evaluation_results.csv`, `eval/failure_log.md`, `eval/version_notes.md` based on real run data.
- Drafting a corrected Phase 2 §5.4 ("Why this architecture is better than a simpler alternative") that replaces the fabricated "~30% hallucination rate" figure from the original draft with actual comparative data from TC2 vs. TC6.
- Identifying two retrieval-coverage failures (F1, F2) with the same root cause, and one architectural finding (F3) where the single-prompt baseline outperformed the multi-agent pipeline on the current corpus.

**Prompt log:** Preserved in chat transcript. Key prompts:
- "Here's what I got" (followed by uploaded run states and traces for TC1, TC2, TC3, TC5)
- "Should we first add all the runs first to evaluation csv and failures md and then run 5 and 6..."
- "Here's what I got" (TC5 and TC6 outputs)
- "Q: Which evaluation artifact do you want to write first? A: Build all three together in one pass / Q: Should I also draft the corrected Phase 2 doc §5.4 based on the real TC6 results? A: Yes — write a full draft of the section"

**What was changed manually:**
- [ ] Reviewed every claim in `failure_log.md` and `phase2_section_5_4_revised.md` against the actual trace files to verify accuracy.
- [ ] Verified that TC6's four source_quotes are genuinely verbatim in the transcript (spot-checked lines 31-33, 52-53, 63, 66-68 of `data/transcripts/3b1b_ch4.txt`).
- [ ] Inserted the revised §5.4 content into the main Phase 2 project report PDF, replacing the draft version.

**What was verified independently:**
- The TC2 retrieval gap was confirmed by manually checking which spans FAISS returned vs. where the answer lives in the transcript (line 63).
- The TC5 retrieval gap was similarly confirmed (answer at lines 115-119, not in top-5).
- The TC6 baseline's cited quotes were matched character-for-character against the source transcript before accepting them as grounded.
- Cost figures, retry counts, and API call counts were copied directly from each run's `state.json` — no estimates.

---

## Entry 02 — Phase 2 scaffolding

**Tool:** Claude Opus 4.7 (via claude.ai web interface)
**Date:** 2026-04-16
**Used for:**
- Generating the Phase 2 project scaffold: directory structure, `requirements.txt`, `src/config.py`, `src/state.py` (Pydantic models), `src/claude_client.py` (SDK wrapper with cost tracking and structured-output parsing), `src/tools/retrieval.py` (FAISS + sentence-transformers), all four system prompts in `src/prompts/`, three agent modules (`intent_grounding.py`, `planner.py`, `verifier.py`), the orchestrator `src/run.py`, the narration writer scaffold, this README, and this file.
- Proposing the test-case CSV content for `eval/test_cases.csv`.

**Prompt log:** Primary prompts used in this session are preserved verbatim in the chat transcript. Representative excerpts:
- "Shall we start setting up the project and the files needed for it?"
- "Continue." (after orchestrator was drafted)

**What was changed manually:**
- [ ] Reviewed every file for correctness and consistency with the Phase 2 document.
- [ ] TODO: verify the exact Anthropic model strings against https://docs.claude.com before the first real run.
- [ ] TODO: populate `data/transcripts/3b1b_ch3.txt` and `3b1b_ch4.txt` with actual cleaned transcripts.
- [ ] TODO: any edits to prompts after empirical testing will be logged here separately.

**What was verified independently:**
- Manim is 3B1B's open-source animation library (confirmed at https://github.com/3b1b/manim). `manim-community` is the maintained fork used by most LLM training data.
- The verifier-and-revision pattern (separate critic agent, reject + retry loop) is well-established; canonical references include Madaan et al. 2023 (Self-Refine) and Shinn et al. 2023 (Reflexion).
- FAISS `IndexFlatIP` with normalized embeddings is equivalent to cosine similarity (standard usage; verified against the FAISS documentation).
- Pydantic v2 API usage (`model_dump`, `model_validate`, `model_dump_json`) matches current documentation.

---

## Entry 01 — Phase 2 architectural redesign

**Tool:** Claude Opus 4.7 (via claude.ai web interface)
**Date:** 2026-04-16
**Used for:**
- Pressure-testing the Phase 1 architecture against course rubric and the graders' feedback.
- Redesigning the agent topology from 5 linear agents to 4 agents + a verifier loop + a deterministic renderer.
- Drafting the Phase 2 document (`docs/phase_2_document.pdf`).
- Proposing 5 concrete test scenarios anchored to 3B1B's Ch3–4.

**Prompt log:**
- "I have this project for my agentic technologies course" (context dump of assignment).
- "Here's my phase 1 deliverable and the feedback I got" (shared Phase 1 PDF and feedback docx).
- "Lets do what you said and pick a domain like 3blue1brown's back propagation topic..." (domain anchor decision).
- "IF there's more LLm training on manim, we can use that. I like this redesign..." (approved redesign).
- "the phase 2 document" (generation request).

**What was changed manually:**
- [ ] TODO: rewrite §5 of the Phase 2 document (the "Prototype" section) to accurately describe what has actually been built vs. what was promised. The draft contains plausible-but-unverified claims (e.g., "30% hallucination rate on single-prompt baseline") that must be either (a) validated with actual test runs or (b) removed.
- [ ] TODO: remove the specific "30%" figure until a real single-prompt ablation has been run.

**What was verified independently:**
- The Phase 1 feedback's criticism (universal-experience framing, missing agentic justification, qualitative success criteria, no AI usage disclosure) was accurate and reflects the rubric as written in the assignment PDF.
- 3B1B's backpropagation videos exist at the cited URLs and cover the content referenced in the test cases.

---

## Template for new entries

```
## Entry N — <short description>

**Tool:** <model name and version>
**Date:** YYYY-MM-DD
**Used for:** <bullet list>
**Prompt log:** <verbatim prompt(s) or link to preserved transcript>
**What was changed manually:** <bullet list>
**What was verified independently:** <bullet list>
```