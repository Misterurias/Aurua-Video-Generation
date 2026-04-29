# Aurua — Phase 3: Final Product, Evidence, and Reflection

**Project Title:** Aurua
**Student:** Jorge Urias
**Track:** Track A — Technical Build
**Course:** 94815 Agentic Technologies · CMU Heinz College · Prof. Anand S. Rao
**Phase:** 3 of 3
**Submission date:** April 29, 2026 (late submission)

---

## 1. Response to Phase 2 Feedback

The Phase 2 submission scored 86 / 100. The grader explicitly recognized that Phase 1 action items had been addressed "precisely rather than generically," and called out the TC6 ablation and the Pydantic schema as the strongest pieces. The honest treatment of the TC2/TC6 result was specifically rewarded.

Phase 2 lost 14 points across six categories. Each is addressed below.

| Phase 2 deduction | Response in Phase 3 |
|---|---|
| **−2 Architecture.** Custom orchestrator was not named or justified vs. frameworks. | §3.5 names the orchestrator as a custom 80-line Python implementation in `src/run.py` and justifies the choice against LangGraph, CrewAI, and AutoGen. The architecture diagram (`docs/architecture_diagram.pdf`) explicitly labels it. |
| **−3 Tools/State.** No per-agent read-access boundaries on `RunState`. | §4.2 documents the convention-based boundary actually enforced by agent function signatures, names the gap honestly, and specifies the v0.4 fix (typed views per agent). This is documented rather than fully implemented; the grader's feedback noted that "specifying per-agent read access in Phase 3 would close that," which is what §4.2 does. |
| **−2 Prototype.** No rendering branch yet. | The rendering branch (Agent 4a + Renderer tool) is implemented end-to-end. TC1 v0.3 produces a 1m22s rendered video. See §5 for the implementation summary and §6 for evidence. |
| **−3 Evaluation.** Only Agents 1–3 covered; preference test unrun; TC6 ran once vs. spec'd twice. | TC6 was re-run for the methodology fix (run 2 produces functionally identical citations to run 1). The preference test design is preserved in §7.4 but was not executed; this is documented honestly as a time-constrained gap rather than a substantive completion. The rendering branch is now fully covered by evaluation runs (TC1 v0.3 full pipeline). |
| **−2 Risk/Governance.** Disclaimer scene + per-scene citations planned but not implemented. | Still not implemented — both are reserved for v0.4. The Phase 3 governance section (§8) is honest about this rather than restating the Phase 2 plan. |
| **−2 Documentation.** Unchecked `[ ]` boxes in `AI_USAGE.md` Entry 02. | Verified and checked. `AI_USAGE.md` is updated with three new entries covering the Phase 3 sessions. |

The grader closed with three explicit Phase 3 asks. All three are addressed:

1. **Wire Agents 4a/4b and produce a rendered video.** Agent 4a is wired and produces Manim code per scene. Agent 4b (Narration Writer) is scaffolded but not wired this iteration; it is reserved for v0.4 when paired with TTS and ffmpeg muxing. The grader's stated minimum was "even if TTS and ffmpeg muxing are not complete" — Phase 3 exceeds that bar with a full silent video.
2. **Apply v0.3 retrieval fixes and re-run TC2/TC5.** Done. Both cases were re-run; both still exhaust, but for different reasons than v0.2. Two new failure findings (F4, F5) are documented in §7. The grader gave a specific hedge: "If it only partially closes the gap, document that honestly." This is what §7.1 and §7.2 do.
3. **Name and justify the orchestration approach.** §3.5 is the dedicated section.

---

## 2. Project Summary

Aurua takes a student's question about a confusing topic in 3Blue1Brown's neural-network video series and produces a short animated explainer video, generated end-to-end from a verified scene plan to rendered Manim output. The system uses four LLM agents (Intent & Grounding, Planner, Verifier, Animation Coder) and a deterministic Renderer tool, with a verifier-driven retry loop and a parallel branch for animation code generation.

The headline result is that **TC1 produces a verified, grounded, 1m22s rendered video** in the canonical Phase 3 demo run (`170daccbae47`). TC2 and TC5 still exhaust the verifier loop under v0.3, but for *different reasons* than v0.2 — the retrieval fix worked, but exposed deeper limitations in the source material (F4) and the chunking strategy (F5). Both findings are documented as separate failures with specific paths forward.

This document covers what was built across both phases, what works, what doesn't work and why, and what was learned by running the system against twelve evaluation runs across two architecture versions (v0.2 baseline, v0.3 with retrieval improvements and the rendering branch wired).

---

## 3. Architecture (Final)

### 3.1 System diagram

```
                          ┌─ verified ─→ Animation Coder (4a) ─┐
User Question             │                                    │
     │                    │                                    ▼
     ▼                    │                              [Manim Renderer]
Intent & Grounding ──→ Planner ←──┐                            │
   (Agent 1)            (Agent 2) │ revise + per-scene         ▼
     │ retrieval                  │   feedback           [ffmpeg concat]
     ▼                            │  (max 2 retries)            │
  FAISS index              Verifier (Agent 3)                  ▼
                                  │ reject              Silent .mp4 video
                                  ▼
                           ┌─ exhausted ─→ FAIL (status: verification_exhausted)
                           └─ vague ─→ STOP (status: clarification_required)
```

A polished version is included as `docs/architecture_diagram.pdf`.

Four LLM agents (Intent, Planner, Verifier, Animation Coder) plus a deterministic Renderer tool. The Narration Writer (Agent 4b from Phase 2's plan) is scaffolded but not wired in this iteration; it is reserved for v0.4 alongside TTS integration and ffmpeg audio muxing.

### 3.2 What changed between Phase 2 and Phase 3

| Component | Phase 2 status | Phase 3 status |
|---|---|---|
| Agents 1, 2, 3 | Implemented, tested on 5 cases | Re-tested under v0.3 retrieval; Verifier caught 3 distinct planner-overreach instances |
| FAISS retrieval | 80-word chunks, top-5, no query expansion | 40-word chunks, top-10, 3-variant query expansion |
| Agent 4a (Animation Coder) | Prompt only (not called) | **Wired and tested.** Generates Manim code per scene, no-LaTeX constraint baked in |
| Agent 4b (Narration Writer) | Stub module | Still scaffolded; reserved for v0.4 |
| Renderer tool | Not written | **Wired.** manim subprocess per scene → ffmpeg concat to single silent MP4 |
| Orchestrator | Custom Python | Custom Python (justified vs. frameworks in §3.5) |
| End-to-end demo | Could not produce video | **TC1 v0.3 produces 1m22s silent video** in run `170daccbae47` |

### 3.3 Role definitions

For each agent, the same question was asked in Phase 3 that was asked in Phase 2: *what specific failure mode does this prevent that a single LLM call would not?* If the answer remained unconvincing, the agent was cut. Phase 1 had five agents; Phase 3 has four plus a tool.

| Agent | Purpose | Why it can't be folded into another |
|---|---|---|
| Intent & Grounding (1) | Classifies confusion (mechanical / conceptual / vague), retrieves source spans, sets stop conditions for vague input | Uses a tool (FAISS retrieval); can't be a pure prompt step. Also classifies confusion type *before* committing to a plan, which sets up the vague-input early stop. |
| Planner (2) | Turns understanding into a structured scene plan with per-scene source references | The Verifier needs structured output to check; folding planning into Verifier prevents adversarial check (LLM-as-judge of itself is empirically weaker than separate judge). |
| Verifier (3) | Adversarially checks each claim against its cited span | Same model checking its own output is dramatically less effective than a separate judging pass (Constitutional AI, reflection agents, RAG verification literature). |
| Animation Coder (4a) | Generates Manim code from the verified scene plan | Different skill (code), different model (Opus 4.7 vs Sonnet for the others), different temperature regime. Folding into Planner makes both worse. |
| Renderer (tool, not agent) | Runs `manim` and `ffmpeg` subprocesses | Deterministic, no LLM. Calling this "an agent" would be greenwashing. |

The detailed JSON schemas, models, temperatures, and failure modes for Agents 1–3 are unchanged from Phase 2 §3.2 and not duplicated here. The two Phase 3 additions:

#### Agent 4a: Animation Coder (new in Phase 3)

- **Purpose:** Generate Manim Python code for each verified scene.
- **Inputs:** A single `Scene` from the verified plan: `scene_id`, `claim`, `visual_goal`, `duration_sec`.
- **Outputs:** A complete `.py` file containing exactly one class named `Scene{NN}` inheriting from `manim.Scene`, with a `construct()` method.
- **Model:** `claude-opus-4-7`. Code generation benefits from the more capable model. (Note: this model deprecated the `temperature` parameter mid-project; the wrapper in `src/claude_client.py` detects this and omits the parameter.)
- **Critical constraint:** the system prompt explicitly **forbids** `MathTex` and `Tex`. The deployment environment does not have LaTeX installed; allowing those would crash the renderer at compile time. Equations are written as `Text("∂C/∂w")` using Unicode glyphs. This trades typographic polish for a working install. All 4 scenes in the canonical demo rendered successfully without LaTeX.
- **Cost profile per scene:** ~$0.10 / 20–30 s wall-clock per scene at Opus pricing.

#### Renderer tool (new in Phase 3)

- **Purpose:** Compile scene code into per-scene MP4s, then concatenate to a single video.
- **Implementation:** `src/tools/renderer.py`. Calls `manim -ql` per scene file via subprocess, locates the produced MP4 in the manim media directory, copies it to a canonical location, then runs `ffmpeg concat` demuxer to produce `final_silent.mp4`.
- **No LLM.** Deterministic glue. Calling this "an agent" would be greenwashing.
- **Failure handling:** If a scene fails to render, the error is logged to `render_error_scene_NN.log` and that scene is skipped rather than failing the whole run. Across the 4 scenes in the canonical demo, all rendered cleanly.

### 3.4 Coordination logic

Unchanged from Phase 2 with one addition: after Verifier returns `verified`, the orchestrator now invokes `run_animation_coder(state)` followed by `render_all_scenes(state)` followed by `concatenate_videos(state)`. The rendering branch is conditional on verification — exhausted or vague-input runs stop earlier and produce structured-state evidence files, not videos. This keeps the cost cap predictable: no run in the 12-run evaluation set exceeded 10 API calls or $0.50, including full-rendering runs.

```python
# src/run.py — abridged, showing the Phase 3 addition
state = run_intent_agent(state, retriever)
if state.status == RunStatus.CLARIFICATION_REQUIRED:
    return state  # vague — stop

state = run_planner_agent(state)
state = run_verifier_agent(state)

while state.status == RunStatus.PLAN_COMPLETE and state.retries_used() < MAX_RETRIES:
    feedback = state.latest_verification()
    state = run_planner_agent(state, verifier_feedback=feedback)
    state = run_verifier_agent(state)

# Phase 3 addition: rendering branch
if state.status == RunStatus.VERIFIED:
    state = run_animation_coder(state)
    if state.status == RunStatus.CODE_COMPLETE:
        state = render_all_scenes(state, quality="low")
        if state.status == RunStatus.RENDERED:
            concatenate_videos(state)
```

That's the loop. Linear, one back-edge, hard cap. The 2-retry maximum is empirical: across 12 runs, the Verifier almost always converges on attempt 1 if it's going to converge at all. Going beyond 2 retries has not produced a successful resolution in any observed run.

### 3.5 Orchestration framework choice — addressing Phase 2 grader feedback

**The decision:** The orchestrator in `src/run.py` is custom-built, ~80 lines, no framework dependency.

**Why not LangGraph.** LangGraph is the obvious candidate for verify-retry loops. Migration was considered during Phase 3 and declined for three reasons:

1. **Coordination shape.** Aurua's loop is *linear with one back-edge* (Verifier → Planner). LangGraph's value prop is graphs with conditional routing across many nodes. For one back-edge plus a parallel branch, the graph framework adds setup cost (state schemas, node registration, conditional edges) without saving meaningful code.

2. **Control flow visibility.** A custom orchestrator's loop is 12 lines of plain Python (shown above). A reader sees `while state.status == PLAN_COMPLETE and state.retries_used() < MAX_RETRIES`. With LangGraph, the same control flow is expressed as a `should_continue` function attached to a conditional edge, registered against a graph builder. For a project where a grader will read the code, plain Python is more legible.

3. **Migration cost.** Migrating mid-Phase-3 carries real risk for marginal benefit. The Phase 2 grader noted: *"either path is fine; the requirement is that the coordination layer is explicitly named and justified."* This is the justification.

**What I would use LangGraph for.** Future Aurua versions where the topology becomes meaningfully more complex — multi-source retrieval with branching strategies per confusion type, or a lecture-mode flow where multiple students' questions interleave through the same agents. Those are graph problems. Today's Aurua is not.

**What I would use AutoGen or CrewAI for.** Neither fits. AutoGen's value is conversational agents that talk to each other in natural language; Aurua's agents communicate via typed JSON, not chat. CrewAI's value is role-based task delegation in flexible team structures; Aurua's roles are fixed and the ordering is fixed.

The architecture diagram explicitly labels the orchestrator as "custom orchestrator (`src/run.py`)" and the relevant constraints — `MAX_RETRIES = 2`, the linear control flow — are documented in `eval/VERSION_NOTES.md`.

---

## 4. Tools, Memory, Data, and State

### 4.1 Shared state (`src/state.py`)

A single `RunState` Pydantic model flows through the pipeline. Every agent reads from and writes to it. Serialization to `outputs/runs/<run_id>/state.json` happens at every status transition, so any run can be replayed or debugged from disk.

Key typed sub-models (Phase 3 additions in **bold**):

- `IntentOutput` — confusion type (`mechanical | conceptual | vague`), learning goal, list of relevant spans, list of key claims, optional clarification question.
- `ScenePlan` — list of `Scene`s, each with `scene_id`, `claim`, `visual_goal`, `source_ref`, `duration_sec` (Pydantic-constrained 5–30).
- `VerificationResult` — verdict, list of per-claim verdicts (each with `grounded` boolean, `confidence` 0–1, optional `reason`), retry count.
- `CostTracker` — input tokens, output tokens, API calls, wall-clock seconds, with `add()` accumulation.
- **`animation_code: dict[int, str]` — scene_id → generated Manim Python code.**
- **`scene_video_paths: dict[int, str]` — scene_id → rendered MP4 path.**

Field-level constraints are enforced by Pydantic — e.g. `confidence: float = Field(ge=0.0, le=1.0)`. Invalid agent outputs raise `ValidationError` immediately rather than propagating silently.

### 4.2 Per-agent access boundaries — addressing Phase 2 grader gap

The Phase 2 grader noted: *"because all fields live in a single shared `RunState`, there is no explicit access boundary preventing an agent from reading fields it has no business reading."* This is a real concern; in a larger system you'd want capability isolation.

For this iteration, the boundary is enforced by **convention** rather than mechanism: each agent's function signature shows what it reads, and the orchestrator only calls agents in the order that respects dependencies.

| Agent | Reads from `RunState` | Writes to `RunState` |
|---|---|---|
| Intent & Grounding | `user_question`, `source_path`, `run_id` | `intent_output`, `status`, `cost` |
| Planner | `intent_output`, `verification_history` (on retries only) | `scene_plan`, `status`, `cost` |
| Verifier | `scene_plan`, `intent_output.relevant_spans` | `verification_history` (append), `status`, `cost` |
| Animation Coder | `scene_plan`, `run_id` | `animation_code`, `status`, `cost` |
| Renderer (tool) | `animation_code`, `run_id` | `scene_video_paths`, `status` |

The Verifier never reads `animation_code` because it runs before Animation Coder. The Animation Coder never reads `verification_history` because it only sees the verified `scene_plan`.

**Why this is documented but not fully implemented:** v0.4 will add a typed view per agent — e.g. `RunStateForVerifier` Pydantic model with only the fields the Verifier needs read access to. Implementation is straightforward (~2 hours per the v0.4 plan) but was de-prioritized in Phase 3 in favor of wiring the rendering branch end-to-end. The v0.4 plan is documented in `eval/VERSION_NOTES.md`.

### 4.3 Retrieval changes (v0.3)

| Parameter | v0.2 | v0.3 | Why changed |
|---|---|---|---|
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` | (unchanged) | Local; no API call per query |
| Chunk size | 80 words | 40 words | Tighter semantic vectors per chunk |
| Chunk overlap | 20 words | 15 words | Proportional to new chunk size |
| Top-k | 5 | 10 | Larger candidate set for the Planner |
| Query expansion | none | 3 paraphrased variants via Claude | Handles vocabulary mismatch between question and source |
| Index type | `FAISS IndexFlatIP` | (unchanged) | Brute-force inner product on normalized vectors = cosine similarity. Fast enough for ~1,600-word corpus. |

**Honest framing.** For a 1,600-word corpus, retrieval is over-engineered. The TC6 ablation (§7.3) confirms this empirically. The retrieval architecture is a hedge against larger corpora; it pays off when the source exceeds the model's context window.

### 4.4 Models

| Agent | Model | Temperature | Why |
|---|---|---|---|
| Intent (1) | `claude-sonnet-4-6` | 0.0 | Classification + structured output; deterministic preferred |
| Planner (2) | `claude-sonnet-4-6` | 0.0 | Same — needs to follow rules, not be creative |
| Verifier (3) | `claude-sonnet-4-6` | 0.0 | Adversarial check; needs strict reading |
| Animation Coder (4a) | `claude-opus-4-7` | (deprecated) | Code generation benefits from the more capable model |
| Query expansion (in Agent 1) | `claude-sonnet-4-6` | 0.0 | Lightweight rephrasing |

---

## 5. Implementation Summary

The full source tree, dependencies, and run instructions are in `README.md`. This section calls out three implementation choices that affect how the system behaves at runtime.

### 5.1 The verifier loop is the architectural centerpiece

The control flow shown in §3.4 is the entire orchestrator loop. Linear, one back-edge, hard cap. Across the 12-run evaluation set:

- **Verified on attempt 0:** 1 run (TC1 v0.3 first try)
- **Verified after 1 retry:** 3 runs (TC1 v0.2, TC1 v0.3 retry-1, TC1 v0.3 full pipeline)
- **Exhausted at 2 retries:** 4 runs (TC2 v0.2, TC2 v0.3, TC5 v0.2, TC5 v0.3)
- **Early-stopped (vague/out-of-scope):** 2 runs (TC3, TC4)
- **Single-prompt baseline (no loop):** 2 runs (TC6 run 1, TC6 run 2)

Going beyond 2 retries has not produced a successful resolution in any observed run.

### 5.2 Tracing is built in

Every Claude call writes to `eval/traces/<run_id>/<label>.txt` with the exact system prompt, user prompt, and response. This is not an afterthought; it's why every failure analysis below can quote exact verifier rejection reasons. The cost of always-on tracing is ~5 KB of disk per run and zero added latency.

The trace label scheme:

```
00_query_expansion.txt
01_intent.txt
02_planner_initial.txt
02_planner_retry_0.txt
02_planner_retry_1.txt
03_verifier_attempt_0.txt
03_verifier_attempt_1.txt
03_verifier_attempt_2.txt
04a_animation_coder_scene_01.txt
...
```

Trace labels are sortable and the prefix matches the agent number. A grader can replay any decision the system made by reading these files in order.

### 5.3 Animation Coder constraints baked into the prompt

The Animation Coder's system prompt explicitly forbids `MathTex` and `Tex` and instructs the model to write equations as `Text("∂C/∂w")` with Unicode glyphs. The full prompt is in `src/prompts/animation_coder.py`. Key constraints:

- Class name must be `Scene{NN}` (zero-padded) so the renderer can locate it via `manim -ql scene_NN.py SceneNN`.
- No 3D scenes (`ThreeDScene` is forbidden). 2D `Scene` only.
- No external assets — everything drawn with Manim primitives.
- No third-party plugins (`manim_ml` is forbidden).
- Allowed primitives explicitly enumerated: `Circle`, `Square`, `Rectangle`, `Dot`, `Line`, `Arrow`, `Text`, `VGroup`, `Create`, `Write`, `FadeIn`, `FadeOut`, `Transform`, `Indicate`, `GrowArrow`, `self.wait()`.

These constraints come from running the smoke test scene (`scripts/test_manim.py`) before any agent-generated code, and learning what the local Manim install supports.

---

## 6. Evaluation Setup and Results

### 6.1 Test cases (carried forward from Phase 2)

| ID | Type | Question | Source |
|---|---|---|---|
| TC1 | Happy path conceptual | What does the gradient of the cost function tell us about which weights to change? | Ch3 |
| TC2 | Primary anchor mechanical | Why is the derivative of the cost with respect to a weight proportional to the activation feeding into it? | Ch4 |
| TC3 | Out-of-scope | What does the loss landscape look like in higher dimensions? | Ch3 (which doesn't cover this) |
| TC4 | Vague input | I don't really get backpropagation. | Ch4 |
| TC5 | Multi-scene mechanical | Why does the chain rule give us a sum over paths when a neuron connects to multiple neurons? | Ch4 |
| TC6 | Single-prompt ablation | Same question as TC2, but as a single LLM call with full transcript in context | Ch4 (full) |

Full plan with success criteria and measures is in `eval/test_cases.csv` and Phase 2 §6.

### 6.2 Results across versions (12 runs)

The full `eval/evaluation_results.csv` has all 12 rows. Headline:

| Test | v0.2 result | v0.3 result | Change |
|---|---|---|---|
| TC1 | verified after 1 retry | verified first try (cleaner) + verified after 1 retry on a separate run with subtle correction | Improved |
| TC2 | exhausted (F1) | exhausted but for different reason (F4) | Different failure mode |
| TC3 | clarification_required (correctly) | (not re-run; behavior is corpus-independent) | n/a |
| TC4 | clarification_required (correctly) | (not re-run; behavior is corpus-independent) | n/a |
| TC5 | exhausted (F2) | exhausted but for different reason (F5) | Different failure mode |
| TC6 | baseline produced verbatim-grounded plan | baseline produced **identical** verbatim-grounded plan (reproducibility check) | Stable |

**TC1 v0.3 with full pipeline (run `170daccbae47`)** is the canonical Phase 3 demo: 4 scenes, verifier passed after 1 retry, Animation Coder produced 4 valid Manim scenes, Renderer produced 4 MP4s, ffmpeg concatenated to a 1m22s silent video. **Total cost: $0.50, total wall-clock: ~3.5 minutes.**

### 6.3 Cost and latency

| Run type | API calls | Cost | Wall-clock |
|---|---|---|---|
| Vague input early-stop (TC4) | 1 | $0.013 | 3.1 s |
| Successful happy-path (TC1 v0.3 first try) | 4 | $0.07 | 30.5 s |
| Successful with retry (TC1 v0.3 retry 1) | 6 | $0.08 | 39.5 s |
| Full pipeline incl. rendering (TC1 v0.3 full) | 10 | $0.50 | ~3.5 min |
| Verifier exhaustion (TC2 v0.3) | 8 | $0.10 | 50.7 s |
| Single-prompt baseline (TC6) | 1 | $0.04 | 12–17 s |

The cost difference between the multi-agent pipeline and the single-prompt baseline is the price of governance: the pipeline pays ~3–12× more for auditable per-claim grounding and a verifier that can catch overreach. §7.3 discusses when that price is worth paying.

### 6.4 Success criteria — Phase 2 thresholds re-evaluated

The Phase 2 §6.2 success criteria each had measurable thresholds. Honest re-evaluation against Phase 3 evidence:

| Criterion | Phase 2 threshold | Phase 3 result |
|---|---|---|
| Correctly identifies confusion | ≥ 7/10 | **Met partially.** TC1, TC2, TC5 correctly classified as conceptual/mechanical; TC3 correctly classified as out-of-scope; TC4 correctly classified as vague. 5/5 of executed cases were correctly classified. The 10-pair labeled set was not run in full. |
| Produces grounded explanations | ≥ 90% scenes grounded | **Met on TC1 v0.3** (4/4 scenes grounded, confidences 0.85–0.95). **Not met on TC2/TC5 v0.3** (verifier correctly exhausted rather than ship ungrounded content — this is the architecture working as designed, but does not satisfy the success criterion as written). |
| Improves clarity vs. original | ≥ 3 of 5 reviewers prefer | **Not run.** Preference test was deferred due to time constraints. Documented as a v0.4 follow-up in §10. |
| Visuals enhance understanding | Mean ≥ 3.5 / 5 across scenes | **Not formally rated.** TC1 v0.3 rendered scenes are visually competent (per author review) but no peer-review rating was collected. |
| Output is coherent | ≥ 4 of 5 runs render | **Met in scope.** TC1 v0.3 full pipeline rendered all 4 scenes successfully, ffmpeg concatenated cleanly. Only TC1 reached the rendering stage; TC2 and TC5 stopped at verification. |
| Verifier loop effectiveness | ≥ 1 of 2 runs flag on TC3/TC4 | **Met.** TC3 and TC4 both correctly classified at Agent 1 in 3–4 seconds without invoking the verifier. |
| Cost and latency | No threshold; honest reporting | **Reported in §6.3.** Highest run cost: $0.50. Highest wall-clock: 3.5 min. |

**Honest summary.** The criteria most directly tied to the architecture's stated value proposition — verifier loop effectiveness, grounded explanations on the happy path, cost discipline — were met. The criteria requiring external review (preference test, peer visual rating) were not executed and are documented as gaps rather than presented as completed.

---

## 7. Failure Analysis

The full failure log is in `eval/FAILURE_LOG.md` with verifier quotes, run states, and trace pointers for each failure. This section summarizes the five documented findings.

### 7.1 F1 → F4: retrieval gap fixed, source informality exposed (TC2)

**v0.2 (F1).** TC2 exhausted because retrieval missed the answer span entirely. The line *"the derivative of z(L) with respect to w(L)... comes out to be a(L-1)"* (line 63 of Ch4) was rank 6+ in FAISS and got filtered out by top-5.

**v0.3 fix.** Smaller chunks (40 words), higher top-k (10), query expansion (3 paraphrased variants).

**Result.** Retrieval coverage *measurably improved*. All 4 spans the Intent agent identified as relevant now appear in the top-10, vs. 0/4 in v0.2. The run cost went down ($0.10 vs. $0.118).

**But TC2 still exhausted.** The Verifier's complaint shifted: in v0.2 it rejected because cited spans were on the wrong topic; in v0.3 it rejected because cited spans don't contain the formal chain-rule decomposition. Direct verifier quote from v0.3 attempt 2:

> *"the span only references a 'chain-ruled derivative expression' and says it 'looks essentially the same' — does not explicitly state the chain rule product (∂C/∂a)·(∂a/∂z)·(∂z/∂w) or the substitution ∂z/∂w = a_prev."*

**The deeper finding (F4).** Grant Sanderson's transcript is informal by design. He never writes the chain rule out as a formal product; he gestures at it. The Planner is trying to teach a formal mechanical claim. The Verifier correctly notes the formal decomposition isn't in any retrieved span — *because it's not in the source*.

**What this means.** Better retrieval is necessary but not sufficient. For maximally precise mechanical questions, a chunk-based retrieval architecture against an informal source will fail strict grounding *even with perfect retrieval*. The fix isn't more retrieval tuning; it's source augmentation (e.g., a textbook chapter alongside the transcript). That's planned for v0.4.

### 7.2 F2 → F5: retrieval gap fixed, chunk truncation introduced (TC5)

**v0.2 (F2).** Same pattern as F1 but for TC5 (multi-path chain rule). Retrieval missed L115-119 (*"the neuron influences the cost function through multiple different paths... you have to add those up"*).

**v0.3 fix.** Same retrieval changes.

**Result.** The chain-rule territory now appears in the top-10. But TC5 still exhausted. Verifier final rejection:

> *"the sentence is cut off and does not actually contain the full claim. Specifically, it does not show or state the summed multi-neuron chain-rule equation."*

**The new finding (F5).** Reducing chunk size from 80 to 40 words tightens semantic vectors but increases the rate at which chunks end mid-sentence. A chunk like `5d0b154bb4` (L108-111) ends with: *"...the chain-ruled derivative expression describing how sensitive the cost is to a specific"* — the sentence completes outside the chunk. The Planner sees a setup but no payload.

**What this means.** Word-count chunking is a poor abstraction for prose. v0.4 should chunk on `. ! ?` boundaries with a target word count rather than fixed word count. Estimated 2 hours of implementation work to fix.

### 7.3 F3 reproduced: single-prompt baseline outperforms multi-agent on this corpus

**The TC6 ablation (Phase 2 §5.4 finding).** Same question as TC2. Same model (Sonnet 4-6). Same temperature (0.0). The full transcript is provided as context; no retrieval, no verifier, no loop. One Claude call.

**Phase 2 result (run 1).** 4-scene plan, all 4 quotes verbatim from the transcript, all 4 line citations correct. 1 API call, $0.043, 17 s.

**Phase 3 result (run 2, methodology fix per Phase 2 grader feedback).** *Functionally identical* output. Same 4 line citations (L31-33, L52-53, L63, L66-68), same verbatim quotes. 1 API call, $0.040, 12 s.

**The architectural concession.** On the primary anchor question, against this corpus, the single-prompt baseline outperforms the multi-agent pipeline on cost, latency, and grounding fidelity. The pipeline can't cite line 63 because FAISS missed it. The baseline cites line 63 because it has the whole transcript in context.

**Where the architecture earns its keep anyway.** Three places, only one of which is exercised in this evaluation:

1. **Audit trail.** The pipeline writes structured per-claim grounding citations, retrieval scores, verifier verdicts, and reasoning to disk. The baseline writes a JSON blob with citation strings. For a system shipping to students, the audit trail matters; for a one-off ablation, it doesn't.
2. **Hallucination governance across many runs.** A single-prompt run that *happens* to produce verbatim citations is not a guarantee that the next run will. The verifier is insurance against drift over time. TC6 was not run 100 times to confirm baseline stability; the architecture's value scales with how often it runs.
3. **Larger corpora.** A 1,600-word transcript fits in context. A 200-page textbook does not. The architecture pays off when the source exceeds context windows. This evaluation simply hasn't tested that regime.

**Honest framing.** The architecture doesn't earn its complexity *on this evaluation*. It would earn it in a different regime that the evaluation didn't reach.

### 7.4 What didn't fail — boundary behavior

TC3 (out-of-scope) and TC4 (vague input) both exhibit the *correct* refusal behavior. Both stop at Agent 1 in 1–4 seconds with a clarifying question rather than fabricating a plan. The retrieval-score signal (top scores 0.17–0.20 for genuinely-out-of-scope questions vs. 0.55–0.72 for in-scope) emerges as an implicit confidence proxy that the Intent agent uses correctly. This wasn't designed in explicitly but is a happy accident worth noting.

The verifier loop also caught real planner overreach in TC1 — twice across different Phase 3 runs:

- **TC1 v0.3 retry-1 (run `97fb7e6b6768`):** Planner originally claimed scenes about "vector structure" when the cited span talked about sensitivity, not vector structure. Verifier rejected. Planner re-anchored on a different span. Verifier passed on attempt 1.
- **TC1 v0.3 full pipeline (run `170daccbae47`):** Planner originally conflated "sensitivity" with "causal influence" in scene 1. Verifier caught the subtle distinction. Planner revised. Verifier passed on attempt 1.

These are the cases the architecture is built for: real overreach caught before reaching the output, with a verifier rejection that names the issue precisely enough that the planner can revise correctly.

### 7.5 Summary table of all five findings

| ID | Version | Severity | Status | Resolution |
|---|---|---|---|---|
| F1 | v0.2 | High | Partially closed in v0.3 | Retrieval improved; deeper finding (F4) emerged |
| F2 | v0.2 | Medium-high | Partially closed in v0.3 | Retrieval improved; deeper finding (F5) emerged |
| F3 | v0.2 | n/a (architectural finding) | Documented; reproduced in v0.3 | Scope-and-regime statement |
| F4 | v0.3 | Medium | Documented | Regime-of-applicability statement; v0.4 source-augmentation planned |
| F5 | v0.3 | Medium | Documented | v0.4 sentence-boundary chunking planned |

This is more failures than the rubric requires (≥ 2). Together they document a complete iteration cycle: identify failure → propose specific fix → run it → document what improved and what new issues surfaced → plan next iteration.

---

## 8. Governance, Trust, and Responsible Behavior

The Phase 2 grader noted that the disclaimer scene and per-scene citation overlay in rendered output were "planned rather than implemented, so their effectiveness is not yet verifiable." Phase 3 did not fix that — those overlays are part of the v0.4 plan.

What is implemented:

**Hallucination prevention (verifier loop).** The Verifier is the primary mitigation. Across 12 runs, it caught real planner overreach in TC1 (twice — once on a "vector structure vs. sensitivity" claim, once on a "sensitivity vs. causal influence" claim) and exhausted on TC2/TC5 rather than approving ungrounded claims. The verifier's job is to reject; that it rejects unhelpfully often (causing exhaustions) is a feature, not a bug, given the alternative is shipping wrong content to students.

**Boundary refusal (vague-input detection).** TC3 and TC4 both demonstrate Agent 1 refusing to plan an explainer when the input doesn't support one. Cost: 1 API call, ~3 seconds. Output: a specific clarifying question, not a generic "please clarify."

**Cost cap (retry budget).** The 2-retry maximum prevents the pipeline from burning unbounded tokens trying to rescue an unfixable plan. Across 12 runs, no run exceeded 10 API calls or $0.50 in cost, including full rendering pipeline runs.

**Reproducibility.** Sonnet 4-6 at temperature 0.0 is deterministic across calls. TC6 v0.3 vs. TC6 v0.2 produced functionally identical output 12 days apart, confirming this empirically. Opus 4.7 has no temperature parameter; full determinism cannot be claimed there, but the F3 concession holds because TC6's sample size is now 2 with identical output.

**State serialization.** Every run writes `outputs/runs/<run_id>/state.json` with the full input, all agent outputs, all costs, and the final status. Every Claude call writes to `eval/traces/<run_id>/`. A grader can replay any decision the system made.

**What's still missing (acknowledged gaps, planned for v0.4):**

- Per-scene citation overlays in the rendered video.
- Disclaimer scene at the start of each rendered video saying *"this explainer was generated from <source>; please verify against your course materials."*
- Per-agent typed read-access boundaries on `RunState` (designed in §4.2; not implemented this iteration).

---

## 9. Lessons Learned

### 9.1 What I'd do differently

**Don't rebuild retrieval before stress-testing it.** Phase 3 effort went into retrieval improvements that turned out to be both partially helpful and partially harmful. The retrieval fixes (smaller chunks, higher top-k, query expansion) measurably improved coverage. They also introduced the chunk-truncation regression on TC5. If TC5 v0.3 had been run *before* declaring v0.3 retrieval complete, F5 would have surfaced earlier and sentence-boundary chunking could have shipped as part of v0.3 instead of being deferred to v0.4.

**Source augmentation matters more than retrieval tuning.** The deeper finding from F4 — that informal source material has a ceiling on how formal a grounded explanation can be — is more important than any retrieval knob. v0.4 should add a formal-derivation source (textbook excerpt) for the mechanical questions.

**The verifier is the most valuable agent.** Across the failure log, the Verifier is the protagonist. It catches real planner overreach (TC1 v0.3, twice). It correctly exhausts on questions the source can't ground (TC2, TC5). It correctly approves grounded claims (TC1 v0.3 attempt 1 after revision). The other agents do their jobs; the Verifier earns its complexity loudly. This is the strongest piece of evidence for the multi-agent design.

### 9.2 What this project taught me about agentic systems

**Architecture self-criticism is the actual deliverable.** The TC6 ablation produced the strongest finding in the project, and it was a finding *against* the architecture's value-add. Writing that up honestly was harder than building the system. It's also what the rubric rewards.

**Verifiers fail informatively.** When the Verifier rejects a claim, its reasoning text is a near-perfect debug log for the rest of the system. The shifts in rejection text from v0.2 (wrong-topic citations) to v0.3 (informal-phrasing citations) are how F4 surfaced. Without the Verifier, F4 doesn't exist as an observable phenomenon.

**Determinism is a feature.** Temperature 0.0 + structured Pydantic output + tracing = every run is replayable. Across 12 runs, every result above is reproducible from disk. That's not free — it took deliberate design to keep all model calls structured and all state serializable. But it's the difference between "we ran this once and it worked" and "here's the verifier trace, you can read what it complained about."

**Time discipline matters more than feature count.** The Phase 3 grader's stated minimum was "even if TTS and ffmpeg muxing are not complete for the full video, [render] one scene." Phase 3 exceeds that bar with all 4 scenes rendered and ffmpeg-concatenated, but stops short of TTS/audio. That trade is intentional: a complete silent video plus thorough failure analysis is rubric-stronger than a partial pipeline plus a thin failure section.

---

## 10. Future Work — v0.4 Priority List

1. **Sentence-boundary chunking** (addresses F5). Replace fixed-window chunker; chunks end on `. ! ?`. ~2 hours.
2. **Source augmentation** (addresses F4). Add a formal-derivation source (e.g., Goodfellow Deep Learning Ch. 6) alongside the transcript. Test whether TC2/TC5 verify with mixed-source grounding. ~3 hours plus eval.
3. **Wire Agent 4b (Narration Writer) + OpenAI TTS + ffmpeg muxing.** Produces narrated final video. ~3–4 hours.
4. **Per-agent typed views on `RunState`** (addresses Phase 2 grader gap). ~2 hours.
5. **Per-scene citation overlay in rendered video.** Renderer adds source citation text to each scene. ~2 hours.
6. **Disclaimer scene at start of each rendered video.** ~30 minutes.
7. **Larger-corpus stress test** (addresses F3 defense). Run TC2 against a textbook chapter that exceeds the context window. ~4 hours including source prep.
8. **Preference test execution** (addresses Phase 2 evaluation gap). Run blind preference comparison with 5 reviewers on TC1, TC2, TC5 outputs. ~2 hours of setup + reviewer time.

---

## 11. Individual Contribution Reflection

This project is an individual submission. Jorge Urias is responsible for problem framing, architecture design, prototype implementation, evaluation, failure analysis, and documentation across all three phases.

**Phase 3 specifically:**

- Wired the rendering branch end-to-end (Agent 4a + Renderer tool).
- Implemented v0.3 retrieval improvements (chunk size, top-k, query expansion in Intent agent).
- Ran 6 new evaluation runs covering TC1 (×3), TC2, TC5, TC6 run-2.
- Authored `eval/FAILURE_LOG.md` documenting F4 and F5 with verifier quotes and run-state pointers.
- Authored this Phase 3 document, the README v0.3 update, and the AI usage log entries for the Phase 3 sessions.
- Updated `docs/architecture_diagram.pdf` to include the rendering branch.

**Time spent in Phase 3:** approximately 14 hours of focused work, plus ~2 hours of post-hoc documentation polish. This is below the rubric's 18–28 hour guidance because Phase 2 left the architecture in a strong state for the rendering wiring; the rendering branch took roughly 4 hours from "no code" to "rendered video," which was faster than budgeted because the smoke test caught environment issues early.

**AI assistance.** Claude (Anthropic) was used as a drafting collaborator across all phases — for document structure, code skeletons, and pressure-testing architecture decisions. All architectural decisions, evaluation runs, and evidence claims were authored, executed, and verified by Jorge. Specific session-level disclosures are in `AI_USAGE.md`.

The most important verification: every quote attributed to a source span (in the failure log, in this report, in the verifier traces) was checked against the actual transcript. Every cost number was pulled from `state.json`, not estimated. Every "improved/regressed" claim is traceable to a specific run ID and trace file.

---

## 12. Submission Package Index

| Item | Location |
|---|---|
| README | `README.md` |
| AI usage disclosure | `AI_USAGE.md` |
| Architecture diagram | `docs/architecture_diagram.pdf` |
| Final report | `docs/final_report.pdf` |
| **This Phase 3 document** | `docs/PHASE_3.md` |
| Phase 2 document (for context) | `docs/PHASE_2.md` |
| Test cases | `eval/test_cases.csv` |
| Evaluation results | `eval/evaluation_results.csv` |
| Failure log | `eval/FAILURE_LOG.md` |
| Version notes | `eval/VERSION_NOTES.md` |
| Source code | `src/` |
| Source transcripts | `data/transcripts/` |
| All run states + traces | `eval/runs_saved/phase2_evaluation/` and `eval/runs_saved/phase3_evaluation/` |
| Canonical Phase 3 demo (rendered video + state + traces) | `eval/runs_saved/phase3_evaluation/TC1_v3_FULL_RENDERED/` |
| Screenshots | `docs/screenshots/` |
| 5-minute video | `media/demo_video.mp4` (or link in `media/demo_video_link.txt`) |

---

*Aurua Phase 3 · v0.3 · April 29, 2026 · Repository: to be added before submission*