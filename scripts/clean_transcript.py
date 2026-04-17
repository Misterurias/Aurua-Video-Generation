"""
Transcript cleaner for Aurua.

YouTube auto-captions have no punctuation, so sentence-splitting doesn't work.
Instead this script treats each caption cue as a natural phrase boundary and
produces one phrase per line. Adjacent cues that are strict prefix-extensions
(YouTube's streaming quirk) get collapsed so you don't see
    "here we tackle back propagation the core"
    "here we tackle back propagation the core algorithm behind how"
as two lines.

Usage:

    # 1. Download captions with yt-dlp (you do this part; needs internet):
    yt-dlp --write-auto-sub --sub-lang en --skip-download \\
        -o "data/transcripts/ch3" https://www.youtube.com/watch?v=Ilg3gGewQ5U
    yt-dlp --write-auto-sub --sub-lang en --skip-download \\
        -o "data/transcripts/ch4" https://www.youtube.com/watch?v=tIeHLnjs5U8

    # Produces ch3.en.vtt and ch4.en.vtt

    # 2. Clean them:
    python scripts/clean_transcript.py data/transcripts/ch3.en.vtt data/transcripts/3b1b_ch3.txt
    python scripts/clean_transcript.py data/transcripts/ch4.en.vtt data/transcripts/3b1b_ch4.txt

    # 3. Spot-check the output.
    # Auto-captions misspell technical terms consistently. Fix with sed:
    #   sed -i '' 's/back propagation/backpropagation/g; s/nural/neural/g' data/transcripts/3b1b_ch3.txt

    # 4. Rebuild the FAISS index on the next run:
    rm -rf data/index/
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


# --- VTT structural lines we ignore ---
_TIMESTAMP_LINE = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}\.\d{3}")
_HEADER_LINES = {"WEBVTT"}
_HEADER_PREFIXES = ("Kind:", "Language:", "NOTE")

# --- Inline markup inside caption text ---
_INLINE_TAG = re.compile(r"<[^>]+>")          # <c>, </c>, <00:00:01.234>, etc.
_BRACKET_NOTE = re.compile(r"\[[^\]]*\]")     # [Music], [Applause], etc.
_FILLER = re.compile(r"\b(um+|uh+|er+|hmm+)\b[ ,]*", re.IGNORECASE)
_MULTI_SPACE = re.compile(r"\s+")


def _clean_text_line(line: str) -> str:
    line = _INLINE_TAG.sub("", line)
    line = _BRACKET_NOTE.sub("", line)
    line = _FILLER.sub("", line)
    return _MULTI_SPACE.sub(" ", line).strip()


def _parse_cues(vtt_text: str) -> list[str]:
    """Extract one text block per cue. A cue is the text between two timestamp
    lines (or between a timestamp line and a blank line)."""
    cues: list[str] = []
    current: list[str] = []
    in_cue = False

    for raw_line in vtt_text.splitlines():
        stripped = raw_line.strip()

        if _TIMESTAMP_LINE.match(stripped):
            if current:
                cues.append(" ".join(current))
                current = []
            in_cue = True
            continue

        if not in_cue:
            continue

        if not stripped:
            if current:
                cues.append(" ".join(current))
                current = []
            in_cue = False
            continue

        if stripped in _HEADER_LINES or any(stripped.startswith(p) for p in _HEADER_PREFIXES):
            continue

        cleaned = _clean_text_line(raw_line)
        if cleaned:
            current.append(cleaned)

    if current:
        cues.append(" ".join(current))

    return [c for c in cues if c]


def _collapse_prefix_duplicates(cues: list[str]) -> list[str]:
    """YouTube emits each cue multiple times as it grows. Keep only the final
    longest version of each prefix-extending run."""
    out: list[str] = []
    for cue in cues:
        if out and (cue.startswith(out[-1]) or out[-1].startswith(cue)):
            if len(cue) > len(out[-1]):
                out[-1] = cue
        else:
            out.append(cue)
    return out


def _deduplicate_exact(cues: list[str]) -> list[str]:
    """Drop exact repeats anywhere in the stream."""
    seen: set[str] = set()
    out: list[str] = []
    for cue in cues:
        key = cue.lower().strip()
        if key in seen:
            continue
        seen.add(key)
        out.append(cue)
    return out


def _strip_sliding_overlap(cues: list[str]) -> list[str]:
    """YouTube scrolling captions emit two-line cues where each new cue's first
    line is the previous cue's second line. This leaves each cue's leading
    words duplicated from the prior cue. Strip that leading overlap.

    Example:
        cue 1: "A B C D E F"
        cue 2: "D E F G H I"   (D E F repeat from cue 1)
        cue 3: "G H I J K L"
      After:
        cue 1: "A B C D E F"
        cue 2: "G H I"
        cue 3: "J K L"
    """
    out: list[str] = []
    for cue in cues:
        if not out:
            out.append(cue)
            continue

        prev_words = out[-1].split()
        cur_words = cue.split()
        # Find the longest suffix of prev_words that is a prefix of cur_words.
        # Bounded search keeps this cheap even for long cues.
        max_k = min(len(prev_words), len(cur_words), 40)
        best_k = 0
        for k in range(1, max_k + 1):
            if prev_words[-k:] == cur_words[:k]:
                best_k = k
        if best_k > 0:
            trimmed = " ".join(cur_words[best_k:]).strip()
            if trimmed:
                out.append(trimmed)
            # If the entire cue was overlap, drop it silently.
        else:
            out.append(cue)
    return out


def _join_short_lines(cues: list[str], min_words: int = 6) -> list[str]:
    """After overlap-stripping, some cues become 1–3 words. Glue them onto the
    previous line so chunks aren't full of micro-fragments."""
    out: list[str] = []
    for cue in cues:
        if out and len(cue.split()) < min_words:
            out[-1] = out[-1] + " " + cue
        else:
            out.append(cue)
    return out


def clean_vtt(vtt_text: str) -> str:
    cues = _parse_cues(vtt_text)
    cues = _collapse_prefix_duplicates(cues)
    cues = _deduplicate_exact(cues)
    cues = _strip_sliding_overlap(cues)
    cues = _join_short_lines(cues)
    return "\n".join(cues) + "\n"


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python scripts/clean_transcript.py <input.vtt> <output.txt>")
        return 1

    vtt_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    if not vtt_path.exists():
        print(f"Input file not found: {vtt_path}")
        return 1

    cleaned = clean_vtt(vtt_path.read_text(encoding="utf-8"))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(cleaned, encoding="utf-8")

    n_lines = cleaned.count("\n")
    n_words = len(cleaned.split())
    print(f"Wrote {n_lines} lines / ~{n_words} words to {out_path}")
    print("Spot-check recommended. Then: rm -rf data/index/")
    return 0


if __name__ == "__main__":
    sys.exit(main())