"""
Runbook Retrieval Service — FAISS-backed semantic search.

Embeds all runbooks in `runbooks/` directory using Sentence Transformers,
builds a FAISS flat index, and answers top-k queries at inference time.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import numpy as np

from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)

_FRONT_MATTER_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)


@dataclass
class RunbookHit:
    slug: str
    title: str
    score: float          # cosine similarity [0, 1]
    excerpt: str          # first 300 chars of body


class RetrievalService:
    """
    Singleton-style service: call `build_index()` once at startup,
    then `search(query, top_k)` at request time.
    """

    def __init__(self, runbooks_dir: str = "runbooks"):
        self._runbooks_dir = Path(runbooks_dir)
        self._model = None          # SentenceTransformer — lazy load
        self._index = None          # faiss.IndexFlatIP
        self._meta: List[dict] = []  # [{slug, title, body, excerpt}]
        self._built = False

    # ── Index building ─────────────────────────────────────────────────────

    def build_index(self, force: bool = False) -> None:
        """
        Load all *.md runbooks, embed them, and build the FAISS index.
        Safe to call multiple times (skips if already built, unless force=True).
        """
        if self._built and not force:
            return

        docs = self._load_runbooks()
        if not docs:
            logger.warning("No runbooks found in", path=str(self._runbooks_dir))
            return

        embeddings = self._embed([d["body"] for d in docs])

        try:
            import faiss  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError("faiss-cpu is required. Run: pip install faiss-cpu") from exc

        dim = embeddings.shape[1]
        # Inner-product index on L2-normalised vectors = cosine similarity
        self._index = faiss.IndexFlatIP(dim)
        faiss.normalize_L2(embeddings)
        self._index.add(embeddings)
        self._meta = docs
        self._built = True
        logger.info("Runbook index built", n_docs=len(docs), dim=dim)

    # ── Search ─────────────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 3) -> List[RunbookHit]:
        """Return top-k matching runbooks for a query string."""
        if not self._built:
            self.build_index()
        if not self._meta:
            return []

        q_emb = self._embed([query])
        import faiss  # noqa: PLC0415
        faiss.normalize_L2(q_emb)

        top_k = min(top_k, len(self._meta))
        scores, indices = self._index.search(q_emb, top_k)

        hits: List[RunbookHit] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            doc = self._meta[idx]
            hits.append(
                RunbookHit(
                    slug=doc["slug"],
                    title=doc["title"],
                    score=float(score),
                    excerpt=doc["excerpt"],
                )
            )
        return hits

    # ── Helpers ────────────────────────────────────────────────────────────

    def _load_runbooks(self) -> List[dict]:
        docs = []
        for path in sorted(self._runbooks_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8", errors="replace")
            slug = path.stem
            # Extract title from front-matter or first H1
            title = slug.replace("-", " ").title()
            fm_match = re.search(r'^title:\s*"?([^"\n]+)"?', text, re.MULTILINE)
            if fm_match:
                title = fm_match.group(1).strip()
            # Strip front-matter for body
            body = _FRONT_MATTER_RE.sub("", text).strip()
            excerpt = body[:300].replace("\n", " ")
            docs.append({"slug": slug, "title": title, "body": body, "excerpt": excerpt})
        return docs

    def _embed(self, texts: List[str]) -> np.ndarray:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer  # noqa: PLC0415
            except ImportError as exc:
                raise ImportError(
                    "sentence-transformers is required. Run: pip install sentence-transformers"
                ) from exc
            logger.info("Loading embedding model", model=settings.EMBEDDING_MODEL)
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        embeddings = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.astype(np.float32)


# ── Module-level singleton ─────────────────────────────────────────────────
retrieval_service = RetrievalService()
