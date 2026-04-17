"""
Central configuration for Aurua.

All model names, file paths, and tunable parameters live here so the
rest of the codebase doesn't need environment-variable plumbing.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Paths ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
INDEX_DIR = DATA_DIR / "index"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
RUNS_DIR = OUTPUTS_DIR / "runs"
EVAL_DIR = PROJECT_ROOT / "eval"
TRACES_DIR = EVAL_DIR / "traces"

for d in (INDEX_DIR, OUTPUTS_DIR, RUNS_DIR, TRACES_DIR):
    d.mkdir(parents=True, exist_ok=True)

# --- API keys ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Models ---
# Sonnet for most agents; Opus for code generation where it matters most.
AGENT_MODEL = os.getenv("AURUA_AGENT_MODEL", "claude-sonnet-4-6")
VERIFIER_MODEL = os.getenv("AURUA_VERIFIER_MODEL", "claude-sonnet-4-6")
CODER_MODEL = os.getenv("AURUA_CODER_MODEL", "claude-opus-4-7")
TTS_MODEL = os.getenv("AURUA_TTS_MODEL", "tts-1")

# --- Retrieval ---
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE_WORDS = 80
CHUNK_OVERLAP_WORDS = 20
TOP_K_RETRIEVAL = 5

# --- Pipeline control ---
MAX_VERIFIER_RETRIES = 2
AGENT_TEMPERATURE = 0.0          # deterministic for Agents 1–3
CODER_TEMPERATURE = 0.3          # some variety helps Manim code generation
MAX_TOKENS = 4096

# --- Observability ---
ENABLE_TRACE_LOGGING = True
