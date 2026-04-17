"""
Apply common auto-caption fixes for 3B1B backprop transcripts.

These are the errors YouTube ASR consistently makes on this content.
Run after clean_transcript.py. Edit this file to add more as you spot them.

Usage:
    python scripts/apply_fixes.py data/transcripts/3b1b_ch3.txt
    python scripts/apply_fixes.py data/transcripts/3b1b_ch4.txt
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


# Whole-word case-insensitive replacements.
# The regex approach preserves surrounding whitespace and handles word boundaries.
REPLACEMENTS: list[tuple[str, str]] = [
    # Core domain term
    (r"\bback propagation\b",     "backpropagation"),
    (r"\bback prop\b",            "backprop"),
    (r"\bback-propagation\b",     "backpropagation"),

    # Consistent misspellings
    (r"\bnural\b",                "neural"),
    (r"\bnurons?\b",              "neurons"),
    (r"\brailu\b",                "ReLU"),
    (r"\bre l u\b",               "ReLU"),
    (r"\bzed of\b",               "z of"),          # "zed" -> "z" in math context
    (r"\bdou ble u\b",            "w"),             # rare but happens
    (r"\bheian\b",                "Hebbian"),       # ch3 has "heian theory"

    # Single-letter math variables that got spelled out
    (r"\bweights? and biases\b",  "weights and biases"),  # no-op, placeholder
]

# Substring replacements (applied after regex). Useful for phrases where
# word-boundary regex is awkward.
RAW_REPLACEMENTS: list[tuple[str, str]] = [
    # e.g. nothing for now
]


def apply_fixes(text: str) -> tuple[str, int]:
    total_subs = 0
    for pattern, replacement in REPLACEMENTS:
        text, n = re.subn(pattern, replacement, text, flags=re.IGNORECASE)
        total_subs += n
    for old, new in RAW_REPLACEMENTS:
        if old in text:
            count = text.count(old)
            text = text.replace(old, new)
            total_subs += count
    return text, total_subs


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/apply_fixes.py <transcript.txt>")
        return 1

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        return 1

    original = path.read_text(encoding="utf-8")
    fixed, n = apply_fixes(original)

    if n == 0:
        print(f"No fixes applied to {path}")
        return 0

    path.write_text(fixed, encoding="utf-8")
    print(f"Applied {n} fixes to {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())