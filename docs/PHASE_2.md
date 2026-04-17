# Aurua — Phase 2: Architecture, Prototype, and Evaluation Plan

**Project Title:** Aurua
**Student:** Jorge Urias
**Track:** Track A — Technical Build
**Course:** 94815 Agentic Technologies · CMU Heinz College · Prof. Anand S. Rao
**Phase:** 2 of 3

---

## 1. Response to Phase 1 Feedback

Phase 1 received the following critiques, each addressed in this submission:

| Phase 1 feedback | Response in Phase 2 |
|---|---|
| Problem stated at domain level, not a specific testable problem | The anchor is now a specific artifact: 3Blue1Brown's backpropagation videos (Ch3–4 of the neural networks series) used as both the source content and the quality benchmark. A specific primary test question is defined in §6. |
| Five agents listed, but the case for each was asserted rather than justified | The architecture has been redesigned to four agents plus a deterministic rendering tool. Each agent is justified against a single-prompt baseline in §3.2, and one new agent (the Grounding Verifier) introduces a feedback loop that a single-prompt architecture cannot replicate. |
| Architecture was a linear pipeline with no coordination beyond sequential handoffs | The redesigned architecture includes a verifier-driven retry loop and a parallel branch (animation code and narration generated concurrently). Shared state, stopping conditions, and a human-in-the-loop checkpoint are specified in §3.3. |
| Success criteria were qualitative with no thresholds or measurement methods | All five original criteria have been rewritten with measures, thresholds, and evaluation methods. Two new system-level criteria have been added. See §6.2. |
| Risks listed without mitigations | Each risk now has a concrete mitigation. See §7. |
| No AI usage disclosure | `AI_USAGE.md` is included in the submission package and will be maintained throughout Phase 3. |

---

## 2. Project Summary

Aurua is an agentic system that converts a confusing learning passage plus a student's question into a short (~60–90 second) animated explainer video. The target user is an undergraduate ML student who has encountered a specific step of a derivation they cannot follow. The system retrieves relevant grounding from the source material, plans a scene-by-scene explanation, verifies each planned claim against the source, and generates Manim animation code and a narration script in parallel. A deterministic renderer compiles the code, synthesizes audio, and muxes the final video.

The quality benchmark is 3Blue1Brown's backpropagation videos. Aurua is not expected to match that production quality; the benchmark exists to (a) provide the source transcripts used as grounding, (b) define a concrete visual target so evaluations can compare coverage and correctness, and (c) give the project a well-scoped corpus rather than an open-ended domain.

---

## 3. Architecture

### 3.1 System diagram

The system consists of four LLM-based agents, one deterministic tool, a feedback loop, and a shared run-level state object.

```
                 ┌──────────────────────────────┐
                 │  User input                  │
                 │  (source content + question) │
                 └──────────────┬───────────────┘
                                │
                                ▼
                 ┌──────────────────────────────┐
                 │ 1. Intent & Grounding Agent  │
                 │    → retrieval tool          │
                 └──────────────┬───────────────┘
                                │
                                ▼
                 ┌──────────────────────────────┐
                 │ 2. Explanation Planner       │──┐
                 │    (scene plan + claims)     │  │ reject + flags
                 └──────────────┬───────────────┘  │
                                │                  │
                                ▼                  │
                 ┌──────────────────────────────┐  │
                 │ 3. Grounding Verifier        │──┘
                 │    (per-claim source check)  │
                 └──────────────┬───────────────┘
                                │ pass (max 2 retries)
                                ▼
          ┌─────────────────────┴─────────────────────┐
          ▼                                           ▼
┌──────────────────────┐                  ┌──────────────────────┐
│ 4a. Animation Coder  │                  │ 4b. Narration Writer │
│     (Manim code)     │                  │     (timed script)   │
└──────────┬───────────┘                  └──────────┬───────────┘
           │                                         │
           └────────────────────┬────────────────────┘
                                ▼
                 ┌──────────────────────────────┐
                 │ 5. Renderer (deterministic)  │
                 │    Manim + TTS + ffmpeg mux  │
                 └──────────────┬───────────────┘
                                ▼
                 ┌──────────────────────────────┐
                 │  Final artifact              │
                 │  (explainer video)           │
                 └──────────────────────────────┘
```

A polished version of this diagram is included as `architecture_diagram.pdf`.

### 3.2 Role definitions and justification

Each agent earns its place by producing an output that a single upstream or downstream prompt could not reliably produce.

#### Agent 1: Intent & Grounding Agent

- **Purpose:** Identify what the student is confused about and retrieve the relevant source passages.
- **Inputs:** `source_content` (text transcript), `user_question` (free text).
- **Outputs:**
  ```json
  {
    "confusion_type": "mechanical | conceptual | vague",
    "learning_goal": "one-sentence statement of what to teach",
    "relevant_spans": [{"span_id": "s1", "text": "...", "location": "L42-58"}, ...],
    "key_claims_to_explain": ["claim_1", "claim_2", ...]
  }
  ```
- **Tools:** Vector retrieval over the source content (FAISS or a local similarity search over transcript chunks). This is the tool use that distinguishes this agent from a single-prompt approach.
- **Model:** Claude Sonnet 4.6 (good at structured output, fast enough for this step).
- **Failure modes:** Mislabels a conceptual confusion as mechanical; retrieves irrelevant spans; treats a vague question as specific.
- **Why separate from a single-prompt baseline:** A single prompt could "read the whole transcript and answer," but this scales poorly and foregoes grounding. Using retrieval (a) forces the system to cite source locations, which downstream verification depends on, and (b) keeps the downstream context window small and focused. Removing this agent would either produce ungrounded explanations or exceed context limits on longer sources.

#### Agent 2: Explanation Planner

- **Purpose:** Produce a scene-by-scene plan for the video.
- **Inputs:** Intent agent output.
- **Outputs:**
  ```json
  {
    "scenes": [
      {
        "scene_id": 1,
        "claim": "A weight is a number that scales the input from one neuron to the next.",
        "visual_goal": "Show two neurons with an arrow labeled w between them; activation flows through.",
        "source_ref": "s1",
        "duration_sec": 15
      },
      ...
    ],
    "total_duration_sec": 75
  }
  ```
- **Tools:** None. This is pure planning.
- **Model:** Claude Sonnet 4.6.
- **Failure modes:** Proposes visuals that cannot be rendered in Manim within scope; sequences scenes in a way that skips a pedagogical step; claims things the source does not support.
- **Why separate from the Intent agent:** Intent is about *understanding the learner*; planning is about *structuring a pedagogical sequence*. Separating them lets the verifier operate on the plan independently, which is the core of the agentic loop. A combined "understand and plan" prompt produces less structured output and makes downstream verification much harder.

#### Agent 3: Grounding Verifier

- **Purpose:** For each scene, check whether the cited source span actually supports the claim. Send the plan back to the Explanation Planner with specific flags if any claim fails.
- **Inputs:** Scene plan from Agent 2, relevant_spans from Agent 1.
- **Outputs:**
  ```json
  {
    "verdict": "pass | revise",
    "per_claim_results": [
      {"scene_id": 1, "grounded": true, "confidence": 0.9},
      {"scene_id": 2, "grounded": false, "reason": "Claim states chain rule gives product of partials, but span s3 does not mention chain rule; find different span or rephrase claim."},
      ...
    ]
  }
  ```
- **Tools:** None — operates over structured inputs only.
- **Model:** Claude Sonnet 4.6 used in a verification role. Uses a different system prompt than the Planner so its checking is not biased by the Planner's framing.
- **Retry policy:** Up to 2 revisions. After the second failure, the system surfaces the ungrounded scenes to the user rather than proceeding.
- **Failure modes:** False positives (approves a hallucinated claim); false negatives (rejects a valid claim because the source phrasing differs from the claim phrasing); infinite-loop tendencies if retry logic is buggy.
- **Why separate from a single-prompt baseline:** This is the agent that makes Aurua genuinely agentic. Empirical evidence (LLM-as-judge literature, reflection agents, Constitutional AI) shows that verification by a separate agent with a distinct prompt detects errors that the generating agent misses. Folding this into the Planner as a self-check is measurably less reliable; the model has already committed to its claims and is unlikely to reject them. Removing this agent entirely is the single biggest failure mode the system mitigates, because hallucinated grounding in educational content is exactly the failure Phase 1 flagged as highest-risk.

#### Agent 4a: Animation Coder

- **Purpose:** Generate Manim code implementing each scene's visual goal.
- **Inputs:** Verified scene plan.
- **Outputs:** A `scene_{i}.py` file per scene containing a `Scene` subclass, plus a manifest of expected render outputs.
- **Tools:** File writing; optional code execution to syntax-check.
- **Model:** Claude Sonnet 4.6 or Claude Opus 4.7 (code generation; Opus if early evaluation shows Sonnet's Manim output is unreliable).
- **Failure modes:** Generates Manim code that references nonexistent API methods; produces animations that render but do not match the visual goal; produces scenes that exceed the planned duration.
- **Why parallel with 4b:** Code generation and pedagogical writing are different skills. Different prompts, possibly different models, definitely different temperatures. A single combined prompt produces worse output on both axes — this is a testable claim and is included in the evaluation plan as an ablation.

#### Agent 4b: Narration Writer

- **Purpose:** Write the narration script with timing markers matching the scene plan.
- **Inputs:** Verified scene plan.
- **Outputs:**
  ```
  [scene 1, 0:00–0:15]
  "Let's start with the simplest possible network: just two neurons..."
  [scene 2, 0:15–0:30]
  "Now, the weight connecting them is..."
  ```
- **Tools:** None.
- **Model:** Claude Sonnet 4.6 (writing task).
- **Failure modes:** Script runs long or short relative to planned scene durations; tone is inconsistent (too formal, too casual); references a visual element the animation does not include.
- **Why separate from 4a:** See above. Runs in parallel to save wall-clock time.

#### Tool: Renderer (deterministic)

- **Purpose:** Compile animations and synthesize the final video.
- **Inputs:** Manim code files, narration script with timing markers.
- **Process:** (1) Run `manim -qm scene_{i}.py` per scene; (2) Run a TTS model (initial choice: OpenAI's `tts-1` or a local alternative like Coqui XTTS) on each narration block; (3) Use `ffmpeg` to concatenate video segments and overlay the audio track.
- **Outputs:** `final_video.mp4`, plus per-scene intermediate files.
- **Why this is not an agent:** It makes no judgments. It runs tools in a fixed order. Separating deterministic glue from LLM agents is a design discipline the course rubric rewards.

### 3.3 Coordination logic

- **Who starts:** Agent 1 runs as soon as the user submits input.
- **Handoffs:** All inter-agent communication is structured JSON written to the shared run state. No free-text handoffs. Each agent reads only the fields it needs.
- **Verifier loop:** Agent 3 sets `verdict` to `pass` or `revise`. On `revise`, the Planner receives the `per_claim_results` and regenerates only the flagged scenes. Maximum 2 retries; on third failure, the system drops the ungrounded scenes and renders a shorter video, surfacing what was dropped in the final output.
- **Parallel branch:** After verification passes, Agents 4a and 4b run concurrently. The Renderer blocks on both completing.
- **Stopping conditions:** (1) Successful render. (2) Verifier exhaustion (described above). (3) Any agent returns an error the retry logic cannot recover from → halt and surface the error to the user.
- **Human-in-the-loop point:** Between Agent 3 (pass) and the parallel branch, the system optionally shows the user the scene plan as text and asks "does this address your confusion?" before spending rendering compute. This is opt-in; for evaluation runs it can be skipped.
- **Shared state:**
  ```python
  run_state = {
      "run_id": str,
      "user_question": str,
      "source_content": str,
      "intent_output": dict | None,
      "scene_plan": dict | None,
      "verification_history": list[dict],
      "animation_code": dict[int, str],  # scene_id -> code
      "narration": str | None,
      "render_status": str,
      "render_output_path": str | None,
      "cost_tracker": {"tokens": int, "calls": int, "wall_clock_sec": float}
  }
  ```

---

## 4. Tools, memory, and data design

### 4.1 Tools

| Tool | Used by | Purpose |
|---|---|---|
| Local vector retrieval (FAISS over transcript chunks) | Agent 1 | Retrieve relevant source spans for a given question. |
| File write | Agents 4a, 4b | Emit code and narration to disk for the renderer. |
| Syntax-check (optional Python AST parse) | Agent 4a | Catch obviously broken Manim code before rendering. |
| Manim CLI | Renderer | Compile animations. |
| TTS API (OpenAI `tts-1` initially, Coqui XTTS as local fallback) | Renderer | Synthesize narration audio. |
| ffmpeg | Renderer | Mux video and audio. |

### 4.2 Memory

Aurua has no cross-session memory in Phase 2. Each run is independent. A run-level shared state (described in §3.3) acts as working memory within a single run. Adding cross-session memory (e.g., "this user is a beginner; use simpler analogies") is a deliberate out-of-scope choice — it adds evaluation burden without proving a new capability.

### 4.3 Data

- **Primary source content:** Transcripts of 3Blue1Brown's "What is backpropagation really doing?" (Ch3) and "Backpropagation calculus" (Ch4) from the Neural Networks series. Obtained from YouTube captions, manually cleaned.
- **Test set:** Five question–source-span pairs (see §6.1), hand-crafted and labeled by Jorge.
- **Evaluation data storage:** `/eval/test_cases.csv` with fields `case_id, question, source_ref, confusion_type_label, expected_behavior`.

---

## 5. Prototype
 
A partial implementation of the Aurua pipeline has been built for Phase 2. The prototype covers Agents 1, 2, and 3 (Intent & Grounding → Explanation Planner → Grounding Verifier), wires them through a shared run-state object, and implements the verifier retry loop end-to-end. Agents 4a (Animation Coder) and 4b (Narration Writer) exist as prompt files in `src/prompts/`; the orchestrator does not call them and they are not exercised by any test in this phase. The deterministic Renderer (Manim / TTS / ffmpeg muxing) is not implemented. All four are Phase 3 work.
 
### 5.1 What is implemented and tested in Phase 2
 
- **Retrieval tool** (`src/tools/retrieval.py`): FAISS index with sentence-transformers embeddings. Index is built once per source and cached on disk. Implemented, used in every multi-agent run.
- **Agent 1 — Intent & Grounding** (`src/agents/intent_grounding.py`): Performs retrieval, classifies the question as `mechanical`, `conceptual`, or `vague`, extracts key claims with span references, and short-circuits the pipeline on vague classification rather than generating a plan. Implemented, tested on all five evaluation cases.
- **Agent 2 — Explanation Planner** (`src/agents/planner.py`): Produces a scene-by-scene plan from the verified intent output. When called on a retry, receives the verifier's per-scene feedback and revises only the flagged scenes. Implemented, tested on four evaluation cases.
- **Agent 3 — Grounding Verifier** (`src/agents/verifier.py`): Checks each scene's claim against its cited source span using a distinct system prompt. Produces per-scene verdicts with reasoning when ungrounded. Drives the retry loop. Implemented, tested on four evaluation cases.
- **Orchestrator** (`src/run.py`): Wires the three agents together, enforces the retry budget, persists the full run state, and captures per-call traces for evaluation. Implemented, used in every run.
- **Shared run state** (`src/state.py`): Pydantic models for every agent's input and output, plus cost tracking. Tested by the smoke-test suite (`tests/test_smoke.py`, 9/9 passing).
- **Single-prompt baseline** (`scripts/run_tc6_baseline.py`): Ablation script used for TC6. Not part of the multi-agent pipeline; exists to compare.
### 5.2 What is scaffolded but not wired
 
- **Agent 4a — Animation Coder:** Prompt defined in `src/prompts/animation_coder.py`. No agent module calls it; no Manim code has been generated by this system.
- **Agent 4b — Narration Writer:** Stub module at `src/agents/narration_writer.py` with its prompt. Not called by the orchestrator.
- **Renderer:** Interfaces implied in the design; no code written. Manim compilation, TTS synthesis, and ffmpeg muxing are Phase 3 tasks.
- **Cross-session memory:** Explicitly out of scope; each run is independent by design (see §4.2).
### 5.3 Interaction trace — TC1, the verifier loop working as designed
 
The most useful trace for understanding the prototype's core behavior is TC1, a conceptual question ("What does the gradient of the cost function tell us about which weights to change?"). The run produced a 5-scene plan on the first planner call; the verifier rejected three of those scenes for specific overreach issues; the planner revised the flagged claims; the verifier passed all five scenes on the second attempt. Full run state is saved at `eval/runs_saved/phase2_evaluation/TC1_verified_retry1/state.json`; full prompt-and-response traces are in that directory's `traces/` subfolder.
 
Abbreviated trace:
 
```
[Agent 1] confusion_type=conceptual, 4 of 5 retrieved spans kept
[Agent 2] initial plan: 5 scenes
[Agent 3] attempt 0: scene 1 UNGROUNDED
          reason: "span 349677eae5 briefly references the gradient vector
          in passing while discussing a single component; it does not
          provide the full definitional claim made in scene 1 about what
          the gradient vector is and what each entry measures."
          verdict: revise
[Agent 2] retry 0: revised scene 1 claim to quote the span closely:
          "The gradient vector is built up from the partial derivatives
          of the cost function with respect to all those weights and
          biases, and computing even one such partial derivative... is
          more than 50% of the work needed for the full gradient."
          Also revised scenes 3 and 4.
[Agent 3] attempt 1: all 5 scenes grounded (confidences 0.88–0.95)
          verdict: pass
[Pipeline] status=verified, retries_used=1, 5 api_calls, 60.33s
```
 
The full traces for this run — each showing the system prompt, the exact payload sent to Claude, and the exact response — are in `eval/runs_saved/phase2_evaluation/TC1_verified_retry1/traces/`:
 
- `01_intent.txt` — Agent 1 retrieval and classification
- `02_planner_initial.txt` — first plan
- `03_verifier_attempt_0.txt` — verifier rejection with reasoning
- `02_planner_retry_0.txt` — planner revision
- `03_verifier_attempt_1.txt` — verifier pass
Two additional traces worth noting, both covered in detail in `eval/failure_log.md`:
 
- **TC2 and TC5 exhausted traces** — the verifier correctly refused to approve claims whose cited spans did not contain the asserted facts. The retry loop terminated rather than shipping ungrounded content. Root cause is a retrieval coverage gap, not a planner or verifier defect. See failures F1 and F2.
- **TC3 vague-input trace** — retrieval scores averaged 0.19 (against 0.55–0.70 for in-scope questions), and the Intent agent used that distribution to classify the question as vague and ask a clarifying question. One API call, 3.5 seconds, no plan generated. This is the cheapest possible failure mode and an intended design behavior.
### Summary of prototype coverage
 
| Component | Implemented? | Exercised in evaluation? |
|---|---|---|
| Retrieval (FAISS + MiniLM) | Yes | Every multi-agent run |
| Agent 1: Intent & Grounding | Yes | All 5 multi-agent test cases |
| Agent 2: Planner | Yes | 4 of 5 (TC3 short-circuited on vague) |
| Agent 3: Verifier | Yes | 4 of 5 (same) |
| Orchestrator + retry loop | Yes | Demonstrated on TC1 (1 retry) and TC2/TC5 (budget exhausted) |
| Shared state + trace logging | Yes | Every run |
| Agent 4a: Animation Coder | Prompt only | No |
| Agent 4b: Narration Writer | Stub module | No |
| Renderer | Not written | No |
 

## 5.4 Why this architecture is better than a simpler alternative — and where it is not, yet
 
The natural simpler alternative to the Aurua pipeline is a single prompt: *"Given this source and this question, produce a scene plan with grounding quotes."* Section §5.4 of the Phase 2 document's first draft asserted that this baseline produces hallucinated grounding at a high rate. That claim was written before any ablation had been run. We ran it now, and the results are more interesting — and less flattering to the architecture — than the draft implied.
 
### The ablation
 
Test case TC6 (in `eval/test_cases.csv`) runs the same question as TC2 — the project's primary anchor case — through a single-prompt baseline implemented in `scripts/run_tc6_baseline.py`. The baseline receives:
 
- The full source transcript in context (the transcript is ~1,600 words, well inside the context window)
- The same question
- The same Claude Sonnet 4.6 model at the same temperature (0.0)
- A system prompt asking for the same scene-plan JSON structure, including a `source_quote` and `source_location` field
No retrieval, no Intent agent, no Verifier, no retry loop. Everything the multi-agent pipeline does must be done in one shot or not at all.
 
### Results
 
| Metric | TC2 (multi-agent pipeline) | TC6 (single-prompt baseline) |
|---|---|---|
| Status | `verification_exhausted` | `completed` |
| API calls | 7 | 1 |
| Input tokens | 14,605 | 2,906 |
| Output tokens | 5,316 | 857 |
| Wall-clock time | 69.9 s | 17.0 s |
| Scenes produced | 4 | 4 |
| Scenes grounded in final output | 2 of 4 | 4 of 4 |
| Hallucinated source quotes | N/A (system refused to ship ungrounded scenes) | 0 of 4 — all quotes verbatim and line locations accurate |
 
### What actually happened
 
On this specific question, the single-prompt baseline outperformed the multi-agent pipeline on every comparable axis: correctness, cost, latency, and grounding fidelity. Its scene 3 correctly cites line 63 of the transcript — *"The derivative of z(L) with respect to w(L)... In this case comes out to be a(L-1)"* — which is exactly the span the multi-agent pipeline's retrieval layer failed to surface in TC2.
 
This is not a defect in the Planner or Verifier. Both worked as designed. The Planner tried to construct a plan from the spans retrieval gave it; the Verifier correctly refused to approve claims whose cited spans did not support them (see `eval/runs_saved/phase2_evaluation/TC2_exhausted/traces/03_verifier_attempt_0.txt` for the rejection reasoning). The architecture failed because its retrieval layer removed the information the rest of the system needed to succeed.
 
This failure recurred identically on TC5, which also required a specific span that FAISS did not retrieve. Two of two mechanical-question cases on Ch4 hit the same coverage gap. See `failure_log.md` F1 and F2 for the full traces.
 
### Where the multi-agent architecture still earned its keep
 
TC1 — a conceptual question about what the gradient tells us — demonstrates the verifier loop working exactly as the architecture promises. The Planner's first draft asserted that each partial derivative *"measures how sensitively the cost responds to a small change in that parameter."* That is a true statement, but the specific span the Planner cited did not say it — the span only mentioned gradient vectors in passing. The Verifier caught this overreach and flagged it for revision. The Planner revised the claim to something closer to what the span actually says: *"The gradient vector is built up from the partial derivatives of the cost function with respect to all those weights and biases... computing even one such partial derivative is more than 50% of the work."* The Verifier passed all 5 scenes on retry 1 with confidences 0.88–0.95.
 
A single-prompt baseline on TC1 could have asserted the same overreach with confident-sounding language and no mechanism would exist to catch it. The multi-agent pipeline did what it was designed to do: catch drift before it reached the output. This is the case the architecture is built for.
 
TC3 — an out-of-scope question about high-dimensional loss landscapes — demonstrates the retrieval-score distribution acting as an implicit scope signal. Top-5 similarities averaged 0.19 on TC3, compared to 0.55–0.70 on TC1, TC2, TC5. The Intent agent used this signal to classify the question as vague and ask a clarifying question rather than generate an ungrounded plan. One API call, 3.5 seconds, no confabulation. A single-prompt baseline given the same question and forced to produce a plan would have had to invent supporting content or state its limitations in prose — neither outcome fits the scene-plan format the task requires.
 
### Honest interpretation
 
Two things are true simultaneously. The verifier agent adds genuine, measurable value — it caught a real overreach in TC1 and it refused to approve ungrounded claims in TC2 and TC5 even when that meant exhausting the retry budget. At the same time, the retrieval layer did not earn its cost on the current corpus. The transcripts used in this evaluation total fewer than 4,000 words combined, which is well inside Claude Sonnet's context window. Retrieval in this regime added a failure mode (coverage gaps) without providing a benefit the baseline could not achieve.
 
The architecture is designed for a regime the current evaluation does not exercise: a corpus too large to fit in context, where the baseline cannot read everything and retrieval becomes necessary rather than performative. Phase 3 will test this by adding a larger-corpus test case (a combined textbook chapter, for example) alongside the Ch3/Ch4 cases.
 
### Fixes planned for Phase 3
 
Documented in `eval/version_notes.md` under v0.3. Three specific changes will be tested:
 
1. Reduce FAISS chunk size from 80 to 40 words to lower the chance of key claims being buried in neighboring context.
2. Raise top-k from 5 to 10 to broaden retrieval's span coverage at the cost of more context per Planner call.
3. Add a lightweight query-expansion step in the Intent agent: for mechanical questions, propose 2–3 alternative phrasings and retrieve against each before consolidating.
After each change, TC2 and TC5 will be re-run. If the pipeline then matches or exceeds the single-prompt baseline on TC6-comparable metrics, the multi-agent architecture is justified within the current corpus. If not, the Phase 3 report will document what further work is needed. This is the kind of test-fix-retest cycle the course rubric's "what changed after testing" criterion calls for, executed in the open rather than post-hoc.
 
### Takeaway
 
The original framing of §5.4 — that the multi-agent pipeline reliably outperforms a single-prompt baseline — was not supported by the data. The actual picture is: the Verifier catches real hallucinations, retrieval currently hurts more than it helps on this corpus size, and the combined system's headline metric is worse than the baseline on 1 of 2 directly comparable test cases. The architectural argument for Aurua is not "the pipeline always beats the baseline"; it is "the pipeline catches specific failure modes the baseline cannot detect, and the pipeline's remaining weaknesses are localized and fixable." The Phase 3 work item is to fix those weaknesses and demonstrate them fixed.

---

## 6. Evaluation plan

### 6.1 Test scenarios

Five scenarios covering happy-path, boundary, and adversarial cases. All are anchored to 3Blue1Brown's Ch3–4 transcripts.

| # | Scenario | Input | Expected behavior | Metric |
|---|---|---|---|---|
| 1 | Happy path, conceptual | "What does the gradient of the cost function tell us about which weights to change?" | Intent identifies conceptual confusion; 3–4 scene plan passes verification on first try; animation code renders; narration matches timing. | Binary pass/fail on each sub-step; end-to-end render success. |
| 2 | Primary anchor, mechanical | "Why is the derivative of the cost with respect to a weight proportional to the activation feeding into it?" | Intent identifies mechanical confusion; plan grounded in specific Ch4 segment; verifier passes; video renders. | Grounded-claims rate ≥ 90%; human reviewer agrees explanation is correct. |
| 3 | Out-of-scope grounding | "What does the loss landscape look like in higher dimensions?" (using Ch3/Ch4 which does not cover this) | Verifier flags insufficient grounding; after 2 retries, system either refuses or produces a video that explicitly notes the source does not cover this. | Verifier correctly flags in ≥ 1 of 2 runs; final output does not hallucinate. |
| 4 | Vague input | "I don't really get backpropagation." | Intent agent classifies as vague and asks a clarifying question rather than generating a plan. | Binary: does the system ask for clarification? |
| 5 | Multi-scene mechanical | "Why does the chain rule give us a sum over paths when a neuron connects to multiple neurons?" | Plan spans multiple scenes; verifier passes; narration stitches scenes coherently. | Grounded-claims rate ≥ 90% across all scenes; video coherence (no abrupt transitions) by human review. |

### 6.2 Success criteria with measures

Each Phase 1 criterion rewritten with a measurable threshold.

| Criterion | Measure | Threshold | Method |
|---|---|---|---|
| Correctly identifies confusion | Intent agent's `confusion_type` matches human label | ≥ 7/10 | 10 hand-crafted (source, question) pairs with labels |
| Produces grounded explanations | % of scene claims with source-supported grounding (human review) | ≥ 90% | ~25 claims across 5 test runs |
| Improves clarity vs. original content | Blinded preference: Aurua explanation vs. raw source passage | ≥ 3 of 5 test users per question | Pairwise preference test with 5 reviewers on 3 questions |
| Visuals enhance understanding | Reviewer rating on 1–5 scale: does visual add information? | Mean ≥ 3.5 across scenes | Per-scene rating by Jorge + 1 peer reviewer |
| Output is coherent | Render success + no >1s dead air + no cut-off narration | ≥ 4 of 5 runs on scenario 1 variants | Manual review of rendered output |
| **System: Verifier loop effectiveness** | Verifier flags problematic claims on scenarios 3 and 4 | ≥ 1 of 2 runs each | Manual review of verifier output |
| **System: Cost and latency** | Tokens per run and wall-clock time | No threshold; honest reporting | Instrumented in run_state |

### 6.3 Evaluation procedure

For each test case, run the full pipeline 2 times (to capture variance). Record the run_state JSON, the verifier history, and the final output. A human reviewer (Jorge + one peer) scores the claim-grounded rate, visual rating, and coherence. Preference testing is run on Scenarios 1, 2, and 5 with 5 reviewers.

Results will be recorded in `/eval/evaluation_results.csv` with fields:
`case_id, run_id, intent_correct, scenes_grounded_pct, verifier_triggered, verifier_retries, render_success, clarity_pref_count, visual_rating_mean, tokens_used, wall_clock_sec, notes`.

### 6.4 Failure analysis protocol

For each failed or partially-failed case, record in `/eval/failure_log.md`:
- What triggered the problem
- What happened (including traces)
- Severity (blocks use / degrades quality / cosmetic)
- Fix attempted
- Current status

This is the Phase 3 deliverable; the protocol is defined here so evaluation generates the data Phase 3 needs.

---

## 7. Risk and governance plan

Each risk now has a concrete mitigation.

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Hallucinated grounding in explanations | High | High (misleads learner) | Grounding Verifier agent with retry loop; manual review in evaluation; surface dropped scenes rather than hide them. |
| Verifier false positives (approves bad claim) | Medium | High | Scenario 4 (injected error) specifically tests this. Use a different system prompt than the Planner to reduce shared bias. If false positive rate exceeds 20% in Phase 3, switch Verifier to Opus 4.7. |
| Manim code fails to render | High initially | Medium | Syntax-check step in Agent 4a; isolate per-scene so one failure does not kill the whole video; keep Phase 3 scope to one well-tested scene template. |
| Intent agent mislabels confusion type | Medium | Medium | Scenario 5 tests cascading failure. If Phase 3 evaluation shows intent accuracy < 60%, add a lightweight user-facing confirmation ("is your confusion about the math or the concept?") before planning. |
| Pipeline latency unacceptable for interactive use | Medium | Low for Phase 3 | Report latency honestly; parallel branch already mitigates; Phase 3 does not promise real-time use. |
| User relies on output without verifying against source | Medium | Medium (education context) | Final video includes an on-screen source citation per scene; a disclaimer scene notes "Aurua can be wrong; verify against the source." |
| Copyrighted source content (3B1B videos) | Low for educational use | Low | Transcripts are used under fair-use research/educational exemption; output explicitly cites source; final submission will not redistribute the transcripts beyond what is required for reproducibility. |
| Cost runs away on verifier retries | Low | Low | Hard cap at 2 retries; cost tracker in run_state; per-run cost logged in evaluation results. |

### 7.1 Governance specifics

- **Boundary behavior:** If the source content does not cover the question, the system refuses rather than confabulates. Scenario 3 is the evaluation of this behavior.
- **Trust:** Every rendered scene includes a visible citation to the source segment it was grounded in. Users can inspect this.
- **Misuse:** The system is pedagogical, not advisory; it produces no recommendations about real-world actions. Misuse potential is low.
- **Reproducibility:** All run_state JSON is saved; a specific run can be replayed from its input, because models are deterministic under `temperature=0` for Agents 1–3 (Agent 4a uses temperature 0.3 to allow Manim code variety).

---

## 8. Contribution update

This project is an individual submission. Jorge Urias is responsible for problem framing, architecture design, prototype implementation, evaluation, and documentation. Because there is only one contributor, the "team plan" reduces to a phased individual timeline:

| Week of | Focus |
|---|---|
| Current → +1 week | Complete Agents 1–3 end-to-end; confirm verifier loop works on scenarios 1–4. |
| +1 → +2 weeks | Complete Agent 4a for scenario 2 (primary anchor); wire renderer for one scene end-to-end. |
| +2 → +3 weeks | Run full evaluation on all 5 scenarios (2 runs each); collect peer reviewer ratings. |
| +3 → Phase 3 due | Failure analysis; record video; final report and submission package. |

Estimated effort matches the rubric's guidance of 10–14 hours for Phase 2 and 18–28 hours for Phase 3.

---

## 9. AI usage disclosure

`AI_USAGE.md` is included in this submission. Summary: Claude was used as a drafting collaborator for the Phase 2 document structure, for pressure-testing the architecture design, and for generating test scenarios. All agent prompts, code, and evaluation design decisions are authored by Jorge and reviewed for accuracy before inclusion. A full prompt log is maintained in `AI_USAGE.md` per course policy.

---

## 10. Appendix: planned directory structure

```
aurua/
  README.md
  AI_USAGE.md
  requirements.txt
  docs/
    phase_2_document.pdf
    architecture_diagram.pdf
    phase_1_document.pdf
  src/
    agents/
      intent_grounding.py
      planner.py
      verifier.py
      animation_coder.py
      narration_writer.py
    tools/
      retrieval.py
      renderer.py
    run.py                 # orchestrates the pipeline
    state.py               # shared run_state definition
  data/
    transcripts/
      3b1b_ch3.txt
      3b1b_ch4.txt
    manifest.csv
  eval/
    test_cases.csv
    evaluation_results.csv  # populated in Phase 3
    failure_log.md          # populated in Phase 3
    traces/
      scenario_4_trace.txt
  outputs/
    scene_1_demo.mp4
  phase_submissions/
    phase1/
    phase2/
```
