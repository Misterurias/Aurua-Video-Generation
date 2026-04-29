# Screenshot Index — Aurua Phase 3

This index documents every visual artifact in `docs/screenshots/`. Each entry follows the rubric template (file, what it shows, why it matters, where it is discussed in the report).

The screenshots together tell the end-to-end Aurua story: a custom student question → grounded scene plan with verifier evidence → generated Manim code → rendered output. Two of the screenshots (03 and 04) deliberately show the verifier in *both* states it can occupy — passing and rejecting — because the verifier loop is the architectural centerpiece of the system.

The canonical Phase 3 demo run referenced throughout this index is **`d79b8b7209a2`**, executed 2026-04-29, against the question *"What does the gradient of the cost function tell us about which weights to change?"* on `data/transcripts/3b1b_ch3.txt`. Final result: 4 scenes verified on first attempt, rendered to a 1m20s silent video, total cost $0.16, total wall-clock 94 seconds.

---

## 01 — CLI invocation

**File:** `CLI_Invocation.png`

**What it shows:** The user-facing entry point. A terminal window showing the index-clear command (`rm -rf data/index/`), the `python -m src.run` invocation with the `--question` and `--source` flags visible, and the first few lines of output as the FAISS index loads from sentence-transformers.

**Why it matters:** Demonstrates that Aurua accepts arbitrary student questions, not pre-registered test cases. The question shown is open-ended and could plausibly come from any reader; nothing about the invocation is specific to TC1 or any other evaluation case. This addresses the rubric's reproducibility requirement — anyone with the repo can run this exact command.

**Where it is discussed in the report:** `docs/final_report.pdf` § 5 (Implementation Summary); `README.md` "Running the pipeline" section.

---

## 02 — Pipeline running end-to-end

**File:** `Pipeline_Running.png`

**What it shows:** The full VS Code workspace with the project tree on the left and the terminal at the bottom showing the complete run output: per-scene Manim renders, ffmpeg concatenation, the `Status: rendered / Retries used: 0 / Cost: 11273 in, 8000 out across 8 calls (94.01s)` summary block, and the structured 4-scene final plan with claims, visual goals, source spans, and durations.

**Why it matters:** This is the rubric's "evidence of agentic behavior" requirement made concrete. A reviewer can see in a single image that (a) all four agents fired, (b) the verifier approved on first try, (c) the rendering branch produced four MP4 files, (d) ffmpeg muxed them into `final_silent.mp4`, and (e) the cost cap held (under $0.20 for a full pipeline run). The structured "Final plan" shows per-scene grounding with span IDs and durations — the audit trail in human-readable form.

**Where it is discussed in the report:** `docs/final_report.pdf` § 5.2 (Results across versions, canonical Phase 3 demo); `docs/PHASE_3.md` § 6.

---

## 03 — Verifier evidence: pass verdict (first-try grounding)

**File:** `Verifier_Evidence.png`

**What it shows:** The contents of `eval/traces/d79b8b7209a2/03_verifier_attempt_0.txt`. The frame captures the input scene plan plus the `--- RESPONSE ---` block at the bottom showing the verifier's structured verdict: `verdict: "pass"`, all four scenes with `grounded: true`, confidences 0.82–0.88, and `retry_count: 0`.

**Why it matters:** This is the rubric's "evidence layer" requirement. The verifier doesn't just emit a yes/no — it emits a structured per-claim verdict with confidences, on disk, in a format anyone can read. Demonstrates that the architecture's grounding claims are auditable. Pair this with screenshot 04 to see the verifier in its other state (rejecting overreach).

**Where it is discussed in the report:** `docs/final_report.pdf` § 5.2 (canonical demo); `docs/PHASE_3.md` § 6.4 (boundary behavior).

---

## 04 — Verifier evidence: revise verdict (catching real overreach)

**File:** `Retry_Loop.png`

**What it shows:** A different verifier trace — `eval/traces/170daccbae47/03_verifier_attempt_0.txt` — showing the verifier rejecting Scene 1 with `grounded: false`, confidence 0.75, and a precise rejection reason: *"The span 5a360a5db7 mentions sensitivity of the cost function to each weight and bias, but does not describe the gradient as a vector with components corresponding to specific weights and biases, nor does it explain the structure of the gradient vector..."* The other three scenes pass; the verdict is `revise`.

**Why it matters:** This is the verifier loop *working as designed* — catching genuine planner overreach before it reaches the student. The rejection reason is specific and actionable; it tells the Planner exactly what's missing from the cited span so a revision can succeed. This is the architectural value proposition of Aurua, captured in a single trace. Together with screenshot 03 (where the verifier passes first try), this pair documents both states of the loop.

**Where it is discussed in the report:** `docs/final_report.pdf` § 5.1 ("The verifier loop is the architectural centerpiece"); `docs/PHASE_3.md` § 6.4 (Verifier loop catches drift in TC1 v0.3); `eval/FAILURE_LOG.md` (the verifier's behavior across all five documented failures).

---

## 05 — State.json: full run audit trail

**File:** `State_json.png`

**What it shows:** `outputs/runs/d79b8b7209a2/state.json` opened in VS Code. The frame shows the complete serialized run state — `intent_output` with key_claims_to_explain, `scene_plan` with all four scenes (scene_id, claim, visual_goal, source_ref, duration_sec), `verification_history`, `animation_code` (the four generated Python files inlined), `scene_video_paths` (four MP4 paths), `cost` (input_tokens 11273, output_tokens 8000, api_calls 8, wall_clock_sec 94), and `status: "rendered"`.

**Why it matters:** Every decision the system made is on disk in a single file. A grader can replay any agent's reasoning by reading this state plus the corresponding trace files. Demonstrates the "auditable grounding" claim that distinguishes the multi-agent architecture from a single-prompt baseline. The `cost` block shows that the cost cap was enforced throughout (8 calls, well under the per-run budget).

**Where it is discussed in the report:** `docs/final_report.pdf` § 4.1 (Shared state design); `docs/PHASE_3.md` § 4.1; `README.md` "Running the pipeline" output section.

---

## 06 — Generated Manim code (Animation Coder output)

**File:** `Generated_Manim_Code.png`

**What it shows:** `outputs/runs/d79b8b7209a2/scenes/scene_02.py` opened in VS Code, showing the complete Manim Python file generated by the Animation Coder agent (claude-opus-4-7). The visible code includes the `class Scene02(Scene):` definition, axes setup (`Axes(x_range=[-3, 3, 1], ...)`), the parabola plot (`axes.plot(lambda w: 0.5 * w**2 + 0.3, ...)`), the descent dot animation, the `negative gradient direction` arrow, and the closing fade-out sequence.

**Why it matters:** Most surprising-to-a-grader artifact in the package. It demonstrates that the Animation Coder agent's output is real, readable, runnable Python — not a magic black box. Note specifically:

- Use of `Text("negative gradient direction", ...)` instead of `MathTex` — the no-LaTeX constraint baked into the system prompt held.
- Only allowed Manim primitives appear (`Arrow`, `Axes`, `Dot`, `Text`, `Create`, `GrowArrow`, `FadeIn`, `FadeOut`, `Indicate`).
- No third-party plugins, no 3D scenes, no external assets.

This makes the agentic-code-generation claim tangible.

**Where it is discussed in the report:** `docs/final_report.pdf` § 4.3 ("Animation Coder constraints baked into the prompt"); `docs/PHASE_3.md` § 3.3 (Agent 4a role definition); `src/prompts/animation_coder.py` (the system prompt that produced this output).

---

## 07 — Final rendered scene (a frame from the explainer)

**File:** `Scene_2_Output.png`

**What it shows:** A frame from `outputs/runs/d79b8b7209a2/videos/scene_02.mp4` (the parabola/descent visualization), captured in VS Code's media preview. The frame shows the final composed visual: a yellow title "Negative Gradient: Steepest Descent", labeled axes (`w` on x-axis, `Cost` on y-axis), the cyan parabola, the green arrow labeled "negative gradient direction" pointing down-and-right toward the minimum, the red descent dot, and the bold yellow "most efficient decrease" caption beneath the axes.

**Why it matters:** This is the final artifact — the thing the rubric category "Final artifact quality and completeness" (worth 20 points) directly evaluates. It demonstrates that the pipeline produces pedagogically meaningful visual output, not just abstract shapes. Every visual element on screen traces back to the verified scene plan in screenshot 02 (claim: "Moving in the direction of the negative gradient adjusts all weights and biases simultaneously..."), grounded in span `09d733b6e3` from `3b1b_ch3.txt:L21-L24`.

**Where it is discussed in the report:** `docs/final_report.pdf` § 5.2 (canonical demo); `docs/architecture_diagram.pdf` (the rendered output node at the bottom of the rendering branch).

---

## 08 — Scene 2 in motion (animation GIF)

**File:** `Scene_2_Output.gif`

**What it shows:** The Scene 2 animation playing through — title fades in, axes draw, parabola is plotted, descent dot appears at the upper-left of the curve, arrow grows pointing down-and-right, "most efficient decrease" caption fades in, dot slides down the curve to the minimum, dot indicates at the minimum. Roughly 20 seconds compressed into a GIF for the submission package.

**Why it matters:** Static frames undersell what the system actually produces. The GIF shows that the visual is animated, paced for pedagogical comprehension (multi-second pauses between visual beats), and delivers on the scene's stated `visual_goal` ("Animate the dot sliding along the arrow toward the minimum"). For graders who won't run the project locally, this is the closest substitute for watching `final_silent.mp4`.

**Where it is discussed in the report:** `docs/final_report.pdf` § 5.2 (rendered artifact); referenced as supporting evidence alongside screenshot 07.

---

## How these screenshots map to the rubric

The Phase 3 rubric weights several categories that these screenshots directly support:

| Rubric category | Points | Screenshots that support it |
|---|---|---|
| Final artifact quality and completeness | 20 | 02, 06, 07, 08 |
| Evidence of agentic behavior or coordination | 15 | 02, 03, 04, 05 |
| Evaluation quality and results | 15 | 02 (canonical demo), 03 (passing verdict), 04 (failing verdict) |
| Failure analysis and iteration | 15 | 04 (verifier rejection), referenced alongside `eval/FAILURE_LOG.md` |
| Governance, trust, and responsible behavior | 10 | 03, 04 (verifier as governance layer); 05 (full audit trail) |
| Documentation, reproducibility, and portfolio quality | 15 | 01 (reproducible invocation), 05 (replayable state), 06 (readable generated code) |

A reviewer who reads only the screenshots and their captions can reconstruct what the system does, why each agent earns its place, and where the architecture's evidence is stored. That is the design intent.