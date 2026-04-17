# Transcript Sources

This file documents the provenance of the source transcripts used as Aurua's grounding corpus for Phase 2 evaluation.

## Source videos

Both transcripts are derived from Grant Sanderson's 3Blue1Brown YouTube series on neural networks. They are used under fair-use educational exemption for a course project; no redistribution outside the submission package is intended.

### `3b1b_ch3.txt`

- **Video:** "Backpropagation, intuitively | Deep Learning Chapter 3"
- **Channel:** 3Blue1Brown
- **URL:** https://www.youtube.com/watch?v=Ilg3gGewQ5U
- **Caption source:** Human-reviewed English subtitles (YouTube "en" track, not auto-generated)
- **Retrieved:** 2026-04-16 via `yt-dlp --write-sub --sub-langs "en"`
- **Content coverage:** ~2,223 words, 185 lines. Focuses on the intuitive walkthrough of backpropagation: what the gradient tells us, how individual training examples "vote" on weight updates, the propagating-backwards idea, mini-batches and stochastic gradient descent.

### `3b1b_ch4.txt`

- **Video:** "Backpropagation calculus | Deep Learning Chapter 4"
- **Channel:** 3Blue1Brown
- **URL:** https://www.youtube.com/watch?v=tIeHLnjs5U8
- **Caption source:** Human-reviewed English subtitles (YouTube "en" track, not auto-generated)
- **Retrieved:** 2026-04-16 via `yt-dlp --write-sub --sub-langs "en"`
- **Content coverage:** ~1,623 words, 130 lines. The formal calculus walkthrough: chain rule setup for a single-neuron-per-layer network, the derivative of the cost with respect to each weight, generalization to layers with multiple neurons.

## Processing pipeline

The raw `.vtt` caption files were processed through two local scripts in `scripts/`:

1. **`clean_transcript.py`** — parses VTT cue boundaries, strips inline timestamp tags, deduplicates the scrolling-caption repetition, joins sliding-window overlap fragments, outputs one phrase per line.
2. **`apply_fixes.py`** — applies a small set of domain-specific term corrections (e.g., normalizing variants of "backpropagation"). Human-reviewed captions required few or no fixes; the script was built for the auto-caption fallback path which was not ultimately needed for these two videos.

No manual transcription or editing of the transcript content was performed beyond the automated cleaning steps described above. The original scripts and VTT files are preserved locally to allow reproduction.

## Why 3Blue1Brown

3Blue1Brown was chosen as the source corpus for three reasons relevant to Phase 2's evaluation design:

1. **Concrete quality benchmark.** The Manim animation library used by Aurua's Phase 3 rendering branch is the same library Grant uses for his videos. This gives the project a tangible visual reference ("can our output come within sight of his quality?") rather than an abstract goal.
2. **Bounded, well-scoped technical content.** Two videos of ~15 minutes each give enough material to test retrieval and grounding without becoming a multi-hour indexing problem.
3. **Pedagogical density.** The content is specifically written to explain one technical concept clearly. Every sentence tends to matter, which makes the Grounding Verifier's job meaningful.

## Attribution

The transcripts are the intellectual property of Grant Sanderson / 3Blue1Brown. They appear in this project solely as evaluation inputs for an academic exercise. Aurua does not redistribute them beyond what is required for the course submission to be reproducible.