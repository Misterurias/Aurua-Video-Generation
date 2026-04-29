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

## Entry 08 — Phase 3 final documentation pass (final report, architecture diagram, README, this file)

**Tool:** Claude Opus 4.7 (via claude.ai web interface)
**Date:** 2026-04-29
**Used for:**

- Drafting `docs/final_report.pdf` (~14-page polished final report) from the comprehensive `PHASE_3.md` source, including report-style visual treatment (amber accent palette, callout boxes for headline findings, dark-themed code blocks, styled blockquotes for verifier rejection quotes).
- Iterating on the report rendering pipeline (pandoc → HTML → wkhtmltopdf), including debugging em-dash rendering in heading fonts and pandoc list-separator behavior.
- Drafting an updated `docs/architecture_diagram.pdf` reflecting the Phase 3 rendering branch (Animation Coder + Renderer at full opacity; Narration Writer faded with v0.4 badge), in the same amber/navy aesthetic as the report.
- Drafting `docs/PHASE_3.md` — the comprehensive Phase 3 document mirroring the structure of `docs/PHASE_2.md`, including grader-feedback response table, success-criteria re-evaluation, and individual contribution reflection.
- Updating `README.md` from Phase 2 status to Phase 3 v0.3 state, including the new architecture flow, Manim setup instructions, expanded evaluation table, F1–F5 summary, and v0.4 priority list.
- Updating this `AI_USAGE.md` file with Entries 04–08 covering all Phase 3 sessions.

**Prompt log:** Preserved in chat transcript. Representative prompts:

- "can you make the report look better? I feel it can visually look a bit better"
- "Q: What visual direction works best? A: Modern technical — sans-serif, colored callouts, subtle backgrounds / Q: Color accent preference? A: Warm orange / amber"
- "Lets move onto the architecture diagram. This is the one from phase 2"
- "Q: How to handle Narration Writer (scaffolded but not wired)? A: Keep Phase 2 implemented agents at full opacity, fade Narration Writer (v0.4)"
- "can we get a Phase_3.md? This is what we had for phase 2"
- "Now lets move onto updating the github readme. This is what we have right now"

**What was changed manually:**

- [x] Reviewed every cost figure, run ID, and citation in the final report against `state.json` files and trace files in `eval/runs_saved/phase3_evaluation/`. Specifically verified `170daccbae47` is the canonical demo run.
- [x] Reviewed every claim in `PHASE_3.md` §6.4 (success-criteria re-evaluation) for honest reporting — confirmed that "not run" or "not formally rated" is used where the criterion was deferred rather than completed.
- [x] Cross-checked the F1–F5 status table in README against `eval/FAILURE_LOG.md`; both agree on partial-closed / documented / reproduced labels.
- [x] Spot-checked architecture diagram against `src/run.py` to confirm the topology shown matches the implemented control flow.
- [x] Replaced the placeholder `_to be added before submission_` repository link in the report and README before final submission.

**What was verified independently:**

- The 12 archived run directories under `eval/runs_saved/phase{2,3}_evaluation/` exist and each contains a `state.json` with the cost numbers cited in the report.
- The canonical demo (`170daccbae47`) actually contains a `final_silent.mp4` and 4 scene MP4s as claimed.
- The architecture diagram's parallel-branch claim (Animation Coder + Narration Writer in parallel) matches the Phase 2 design document, with the visual fading of 4b reflecting that only 4a is wired in v0.3.

---

## Entry 07 — Phase 3 evaluation completion (TC5 v0.3, TC6 run-2) and failure-log expansion

**Tool:** Claude Opus 4.7 (via claude.ai web interface)
**Date:** 2026-04-28 (late night) → 2026-04-29 (early morning)
**Used for:**

- Auditing the Phase 3 work against the Phase 2 grader's three explicit asks before sprinting further on audio (rendering branch ✅, v0.3 retrieval applied to TC2/TC5 ⚠️, orchestration justification ❌).
- Pacing decision: complete missing evaluation runs (TC5 v0.3 with full pipeline, TC6 run-2) before attempting Tier 2 (audio).
- Analyzing the TC5 v0.3 verifier-exhausted result, identifying that the failure mode shifted from F2 (wrong-topic spans) to a chunk-truncation regression introduced by the smaller-chunk v0.3 fix. New finding documented as F5.
- Confirming TC6 reproducibility: run-2 produced functionally identical 4-scene plan with identical line citations (L31-33, L52-53, L63, L66-68) to run-1 from Phase 2, 12 days apart. Stable baseline finding.
- Updating `eval/evaluation_results.csv` with all Phase 3 rows, expanding `eval/FAILURE_LOG.md` with F4 and F5 entries, updating `eval/VERSION_NOTES.md` with v0.3 results and v0.4 plan.

**Prompt log:** Preserved in chat transcript. Representative prompts:

- "Great! Before going into the audio, do we need to do any more runs for the full video pipeline or testing in accordance with the feedback we got and what the project requirements are?"
- "Q: Given the gaps I just listed, which path tonight? A: Hybrid — doc gaps + missing runs first, audio if time permits at end"
- "Q: Should TC5 v0.3 run with rendering or without? A: Run full pipeline — burn the $0.50, get a second rendered video as bonus"
- "Here's what we got" (uploaded TC5 v0.3 traces and state.json)
- "Here's what we got" (uploaded TC6 run-2 state.json)

**What was changed manually:**

- [x] Verified every verifier rejection quote in F4 and F5 was a direct copy from the actual `03_verifier_attempt_*.txt` trace file, not paraphrased.
- [x] Confirmed the chunk-truncation claim in F5 by inspecting the actual chunk text for `5d0b154bb4` (L108-111) — sentence does end mid-thought as described.
- [x] Verified the TC6 run-2 line citations match run-1 character-for-character before claiming "functionally identical."
- [x] Decided F4 and F5 should each be their own failure entry rather than appending to F1/F2, because the failure modes are genuinely distinct.

**What was verified independently:**

- TC5 v0.3 retrieval IS measurably better than v0.2 — confirmed by comparing the retrieved span IDs in `01_intent.txt` for TC5 v0.2 vs. v0.3.
- The chunk-truncation bug is real, not artifactual — verified by reading multiple v0.3 chunks and counting how many end mid-sentence.
- TC6 run-2's API call cost ($0.040) and run-1's cost ($0.043) come from the actual `state.json` files, not estimates.

---

## Entry 06 — Phase 3 rendering branch wiring (Agent 4a + Renderer)

**Tool:** Claude Opus 4.7 (via claude.ai web interface)
**Date:** 2026-04-28
**Used for:**

- Drafting `src/prompts/animation_coder.py` (system prompt with strict no-LaTeX constraint, allowed-primitives list, output-format rules).
- Drafting `src/agents/animation_coder.py` (one Claude call per scene, code-fence stripping, file write to `outputs/runs/<run_id>/scenes/scene_NN.py`).
- Drafting `src/tools/renderer.py` (subprocess calls to `manim -ql`, MP4 location after render, ffmpeg concat demuxer for final video).
- Patching `src/state.py` to add `scene_video_paths: dict[int, str]` field to `RunState`.
- Patching `src/run.py` to invoke the rendering branch after verification passes.
- Patching `src/claude_client.py` to handle the `claude-opus-4-7` deprecation of the `temperature` parameter (conditional kwargs based on model identifier).
- Drafting `scripts/test_manim.py` smoke test to confirm the local Manim install works before invoking the agent pipeline.

**Prompt log:** Preserved in chat transcript. Representative prompts:

- "Q: What's the move? A: Re-run TC1 against the correct source (Ch3) — likely passes, becomes the demo"
- "Here's what I got. The manim test video was created successfully! But we got an error on the first try for the question. The scenes folder in aurua/eval/traces/97fb7e6b6768/ is empty"
- (Pasted: `BadRequestError: temperature is deprecated for this model.`)
- "Here's what we got. It outputted a video of 1 minute 22 seconds and honestly the visuals do not look bad. It's pretty interpretable."

**What was changed manually:**

- [x] Replaced AI-suggested model name `RETRIEVAL_TOP_K` with the actual constant in my config (`TOP_K_RETRIEVAL`); the AI had it wrong.
- [x] Reviewed every line of generated Manim Python code for `MathTex` / `Tex` references before rendering (none found, prompt constraint held).
- [x] Watched the canonical demo (`170daccbae47/final_silent.mp4`) end-to-end and confirmed the visuals match the verified scene plan.
- [x] Archived the canonical demo to `eval/runs_saved/phase3_evaluation/TC1_v3_FULL_RENDERED/`.

**What was verified independently:**

- Manim Community is the correct Manim distribution (`pip install manim`) for the AI-generated code; verified against https://docs.manim.community.
- The Opus 4.7 temperature deprecation is a documented API change, confirmed by reproducing the BadRequestError with a minimal repro before applying the conditional fix.
- ffmpeg concat demuxer behavior matches the documented format (`-f concat -safe 0 -i list.txt -c copy out.mp4`); verified with the actual concat output.
- All 4 generated scene files compile and render under `manim -ql`; verified by inspecting `outputs/runs/170daccbae47/videos/`.

---

## Entry 05 — Phase 3 v0.3 retrieval improvements (TC2 v0.3, TC1 v0.3)

**Tool:** Claude Opus 4.7 (via claude.ai web interface)
**Date:** 2026-04-28
**Used for:**

- Patching `src/config.py` with v0.3 retrieval values: `CHUNK_SIZE_WORDS: 80 → 40`, `CHUNK_OVERLAP_WORDS: 20 → 15`, `TOP_K_RETRIEVAL: 5 → 10`, plus new `ENABLE_QUERY_EXPANSION` and `QUERY_EXPANSION_VARIANTS` flags.
- Drafting the query-expansion logic in `src/agents/intent_grounding.py`: a new `_expand_query()` function that calls Claude to generate 3 paraphrased variants, multi-query retrieval that deduplicates by span_id and ranks by max score across queries.
- Diagnosing the TC1 v0.3 first-pass failure: I had typed `--source data/transcripts/3b1b_ch3.txt` but the FAISS index was still cached from the previous Ch4 run, so retrieval was searching the wrong index. The AI caught the mismatch by inspecting the retrieved span locations in the trace.
- Re-running TC1 against the correct (Ch3) source after `rm -rf data/index/`.
- Analyzing the TC2 v0.3 result: retrieval is measurably better (4/4 of Intent's chosen spans now in top-10 vs. 0/4 in v0.2) but the verifier still exhausts because the formal chain-rule decomposition isn't in any retrieved span — the new finding documented as F4.

**Prompt log:** Preserved in chat transcript. Representative prompts:

- "remind me why we are changing config.py and intent_grounding.py?"
- (Uploaded: TC2 v0.3 state.json and full trace set)
- "Here's what I got" (uploaded TC1 v0.3 first-attempt traces; AI noticed Ch4 spans in the retrieval output)

**What was changed manually:**

- [x] Verified the v0.3 retrieval changes were applied to the correct constants in `config.py` (the AI initially wrote `RETRIEVAL_TOP_K`; corrected to `TOP_K_RETRIEVAL`).
- [x] Confirmed by trace inspection that query expansion produced 3 reasonable paraphrased variants for TC2 (e.g., "rate of change of the error", "sensitivity of the cost function to a particular weight").
- [x] The `rm -rf data/index/` step before TC1 re-run was necessary because the FAISS index doesn't track which transcript it was built from; this is a known limitation of the current retrieval implementation, documented as a v0.4 hardening item.

**What was verified independently:**

- The retrieval rank shift (v0.2 → v0.3) was confirmed by manually comparing the retrieved span IDs in the two runs' `01_intent.txt` traces.
- The verifier rejection reason for TC2 v0.3 attempt 2 was read in full (not just summarized) before being characterized as "informal source phrasing"; the verifier's actual language is preserved verbatim in F4.

---

## Entry 04 — Phase 3 session kickoff and triage

**Tool:** Claude Opus 4.7 (via claude.ai web interface)
**Date:** 2026-04-28
**Used for:**

- Loading and parsing the Phase 2 grader feedback document, mapping each deduction category to the Phase 3 backlog.
- Triaging the remaining work given a same-night deadline (Phase 3 was overdue, Thursday presentation imminent).
- Deciding pacing: tiered approach (Tier 1 = silent rendered video, Tier 2 = audio if time permits, Tier 3 = ffmpeg muxing as stretch).
- Deciding orchestration question: keep custom orchestrator and write justification (rather than migrate to LangGraph mid-deadline).
- Deciding TTS path: OpenAI tts-1 (already-available SDK) over ElevenLabs (would require new signup).

**Prompt log:** Preserved in chat transcript. Representative prompts:

- "Do you remember where we last left off on this project"
- "This is a pdf of our previous chat conversation. We finished phase 2"
- "As a reminder here's the project requirements. We also received feedback on our submission" (uploaded: `Jorge Urias Phase 2 Feedback.docx`)
- "Well I'm already past the due date technically. It was due Sunday and its Tuesday night. We have to work on Phase 3 and try to get it done by tonight or early morning tomorrow."
- "Q: On the rendered video output — what's the minimum bar? A: Try full video + ffmpeg muxing"
- "Q: Tiered build (Tier 1 → 2 → 3) or full send on the audio pipeline? A: Tiered approach — ship whichever tier I reach"

**What was changed manually:**

- [x] Confirmed each Phase 2 deduction category has a corresponding Phase 3 response in `PHASE_3.md` §1.
- [x] Confirmed the orchestration justification text in `PHASE_3.md` §3.5 is consistent with the actual code in `src/run.py` (~80 lines, linear with one back-edge, no framework dependency).

**What was verified independently:**

- The Phase 2 feedback document was read in full before allowing the session to proceed; the AI's summary of the three explicit asks (wire 4a/4b + render, apply v0.3 fixes, name orchestration) matches the feedback text verbatim.
- The grader's hedge ("If v0.3 only partially closes the gap, document that honestly") was preserved as the framing for the F4/F5 writeups rather than ignored.

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

- [x] Reviewed every claim in `failure_log.md` and `phase2_section_5_4_revised.md` against the actual trace files to verify accuracy.
- [x] Verified that TC6's four source_quotes are genuinely verbatim in the transcript (spot-checked lines 31-33, 52-53, 63, 66-68 of `data/transcripts/3b1b_ch4.txt`).
- [x] Inserted the revised §5.4 content into the main Phase 2 project report PDF, replacing the draft version.

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

- [x] Reviewed every file for correctness and consistency with the Phase 2 document.
- [x] Verified the exact Anthropic model strings against https://docs.claude.com before the first real run. Confirmed `claude-sonnet-4-6` and `claude-opus-4-7` as current.
- [x] Populated `data/transcripts/3b1b_ch3.txt` and `3b1b_ch4.txt` with actual cleaned transcripts (downloaded from YouTube captions, cleaned via `scripts/clean_transcript.py` and `scripts/apply_fixes.py`).
- [x] Edits to prompts after empirical testing are logged in subsequent entries (Entry 03 onward).

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

- [x] Rewrote §5 of the Phase 2 document (the "Prototype" section) to accurately describe what was actually built vs. what was promised. The plausible-but-unverified "30% hallucination rate" claim was removed; §5.4 was rewritten in Entry 03 with real TC6 ablation data.
- [x] Removed the specific "30%" figure; the revised §5.4 cites actual TC2 vs. TC6 numbers (7 calls vs. 1, 2/4 vs. 4/4 grounded scenes) instead.

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

---

## Summary of AI assistance across the project

Across all phases, Claude was used as a drafting collaborator for document structure and code skeletons, and as an analytical partner for evaluation interpretation. The pattern:

- **Claude drafted** the document scaffolds, code modules, prompts, and prose.
- **Jorge made** all final architectural decisions, ran all evaluations, and wrote (or rewrote) every claim that affects the rubric grading.
- **Jorge verified** every quote attributed to a source span (against the actual transcript), every cost number (against `state.json` files), and every "improved/regressed" claim (against specific run IDs and trace files).

The most important verification that runs through every entry: any factual claim about what the system did, what it cost, or what the verifier said was checked against the artifact on disk before being included in any deliverable. No claim in the final report, failure log, or this file rests on AI-generated reasoning that wasn't independently confirmed against a real evidence file.