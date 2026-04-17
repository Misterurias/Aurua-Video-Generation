"""
FAISS-based retrieval over transcript chunks.

Architectural note: for a corpus of ~5k words, FAISS is over-engineered
compared to keyword search or even full-context prompting. We use it
anyway because (a) it demonstrates a production-ready retrieval pattern
for a portfolio piece, and (b) the design generalizes cleanly if Aurua
is later extended to larger corpora (full textbooks, multi-video libraries).

The `Retriever` interface is deliberately simple so it can be swapped for
a keyword-search implementation with no changes upstream.
"""
from __future__ import annotations

import hashlib
import json
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from .. import config


@dataclass
class Chunk:
    chunk_id: str
    text: str
    source_file: str
    line_start: int
    line_end: int

    @property
    def location(self) -> str:
        return f"{Path(self.source_file).name}:L{self.line_start}-L{self.line_end}"


@dataclass
class RetrievalHit:
    chunk: Chunk
    score: float


class Retriever:
    """Embed transcript chunks once, then answer similarity queries."""

    def __init__(self, model_name: str = config.EMBEDDING_MODEL) -> None:
        self._model_name = model_name
        self._model: Optional[SentenceTransformer] = None
        self._index: Optional[faiss.Index] = None
        self._chunks: list[Chunk] = []

    # -- model is loaded lazily; it's ~80MB --
    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self._model_name)
        return self._model

    # ------------------------------------------------------------------
    # Index building
    # ------------------------------------------------------------------
    def build_index(self, transcript_paths: list[Path]) -> None:
        chunks = []
        for path in transcript_paths:
            chunks.extend(self._chunk_file(path))

        if not chunks:
            raise ValueError(f"No chunks produced from {transcript_paths}")

        texts = [c.text for c in chunks]
        embeddings = self._get_model().encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        )
        embeddings = np.asarray(embeddings, dtype=np.float32)

        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)  # cosine similarity (vectors are normalized)
        index.add(embeddings)

        self._index = index
        self._chunks = chunks

    def save(self, index_dir: Path) -> None:
        if self._index is None:
            raise RuntimeError("Cannot save: index has not been built.")
        index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(index_dir / "faiss.index"))
        with (index_dir / "chunks.pkl").open("wb") as f:
            pickle.dump(self._chunks, f)
        (index_dir / "meta.json").write_text(
            json.dumps({"embedding_model": self._model_name, "n_chunks": len(self._chunks)})
        )

    def load(self, index_dir: Path) -> None:
        self._index = faiss.read_index(str(index_dir / "faiss.index"))
        with (index_dir / "chunks.pkl").open("rb") as f:
            self._chunks = pickle.load(f)

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------
    def search(self, query: str, top_k: int = config.TOP_K_RETRIEVAL) -> list[RetrievalHit]:
        if self._index is None:
            raise RuntimeError("Index not loaded or built.")
        q_emb = self._get_model().encode(
            [query], normalize_embeddings=True, show_progress_bar=False
        )
        q_emb = np.asarray(q_emb, dtype=np.float32)
        scores, indices = self._index.search(q_emb, top_k)
        hits = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            hits.append(RetrievalHit(chunk=self._chunks[idx], score=float(score)))
        return hits

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------
    def _chunk_file(self, path: Path) -> list[Chunk]:
        """Word-based sliding-window chunks with line tracking.

        Tracking line numbers (not just character offsets) means citations
        point to something a human can actually find in the transcript.
        """
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()

        # Flatten to words with a parallel list of line numbers
        words: list[str] = []
        word_lines: list[int] = []
        for lineno, line in enumerate(lines, start=1):
            for word in line.split():
                words.append(word)
                word_lines.append(lineno)

        chunk_size = config.CHUNK_SIZE_WORDS
        overlap = config.CHUNK_OVERLAP_WORDS
        step = max(1, chunk_size - overlap)

        chunks = []
        for start in range(0, len(words), step):
            end = min(start + chunk_size, len(words))
            if end - start < 10:  # drop tiny trailing fragments
                break
            chunk_text = " ".join(words[start:end])
            line_start = word_lines[start]
            line_end = word_lines[end - 1]
            chunk_id = _short_hash(f"{path.name}:{line_start}-{line_end}")
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    text=chunk_text,
                    source_file=str(path),
                    line_start=line_start,
                    line_end=line_end,
                )
            )
            if end == len(words):
                break
        return chunks


def _short_hash(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:10]


# ----------------------------------------------------------------------
# Convenience constructor
# ----------------------------------------------------------------------
def get_or_build_retriever(transcript_paths: list[Path]) -> Retriever:
    """Load the cached index if present; otherwise build and save one."""
    retriever = Retriever()
    faiss_path = config.INDEX_DIR / "faiss.index"
    chunks_path = config.INDEX_DIR / "chunks.pkl"
    if faiss_path.exists() and chunks_path.exists():
        retriever.load(config.INDEX_DIR)
    else:
        retriever.build_index(transcript_paths)
        retriever.save(config.INDEX_DIR)
    return retriever
