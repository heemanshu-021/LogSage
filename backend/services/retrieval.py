"""
Runbook Retrieval Service — FAISS-backed semantic search with keyword fallback.

Embeds all runbooks in `runbooks/` directory using Sentence Transformers,
builds a FAISS flat index, and answers top-k queries at inference time.

When sentence-transformers or faiss-cpu are unavailable the service degrades
gracefully to a TF-IDF keyword search.  The fallback is clearly labelled as
``search_mode: "lexical"`` in all results so callers can distinguish it from
real semantic similarity.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import numpy as np

try:
    from backend.core.config import settings
    _DEFAULT_EMBEDDING_MODEL = settings.EMBEDDING_MODEL
except Exception:
    import os
    _DEFAULT_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

from backend.core.logging import get_logger

logger = get_logger(__name__)

_FRONT_MATTER_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
# Extract individual YAML front-matter fields
_FM_FIELD_RE = re.compile(r"^(\w+):\s*\"?([^\"\n]+)\"?\s*$", re.MULTILINE)


@dataclass
class RunbookHit:
    slug: str
    title: str
    score: float          # cosine similarity [0, 1]
    excerpt: str          # first 300 chars of body
    search_mode: str = "semantic"   # "semantic" | "lexical"


@dataclass
class RunbookDetail:
    """Full runbook content returned by the incident runbook endpoint."""
    slug: str
    id: str
    title: str
    score: float
    search_mode: str
    # Structured sections parsed from Markdown headings
    symptoms: str
    possible_causes: str
    investigation_steps: str
    remediation: str
    verification_steps: str
    escalation: str
    tags: List[str] = field(default_factory=list)
    full_body: str = ""


def _parse_section(body: str, heading: str) -> str:
    """Extract the text under a Markdown ## Heading (up to the next ## heading)."""
    pattern = re.compile(
        rf"##\s+{re.escape(heading)}\s*\n(.*?)(?=\n##\s|\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    m = pattern.search(body)
    return m.group(1).strip() if m else ""


def _build_runbook_detail(doc: dict, score: float, search_mode: str) -> RunbookDetail:
    body = doc["body"]
    tags_raw = doc.get("tags", "")
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
    return RunbookDetail(
        slug=doc["slug"],
        id=doc.get("id", doc["slug"]),
        title=doc["title"],
        score=score,
        search_mode=search_mode,
        symptoms=_parse_section(body, "Symptoms"),
        possible_causes=_parse_section(body, "Possible Causes"),
        investigation_steps=(
            _parse_section(body, "Investigation Steps")
            or _parse_section(body, "Immediate Triage")
        ),
        remediation=_parse_section(body, "Remediation"),
        verification_steps=_parse_section(body, "Verification Steps"),
        escalation=_parse_section(body, "Escalation"),
        tags=tags,
        full_body=body,
    )


class RetrievalService:
    """
    Singleton-style service: call `build_index()` once at startup,
    then `search(query, top_k)` at request time.

    Falls back to TF-IDF keyword search when sentence-transformers or
    faiss-cpu are not installed.  The fallback is labelled ``search_mode:
    "lexical"`` so callers can distinguish it from real semantic similarity.
    """

    def __init__(self, runbooks_dir: str = "runbooks"):
        self._runbooks_dir = Path(runbooks_dir)
        self._model = None          # SentenceTransformer — lazy load
        self._index = None          # faiss.IndexFlatIP
        self._meta: List[dict] = []  # [{slug, title, body, excerpt, id, tags}]
        self._built = False
        self._semantic_available: Optional[bool] = None  # None = not yet checked

    # ── Index building ─────────────────────────────────────────────────────

    def build_index(self, force: bool = False) -> None:
        """
        Load all *.md runbooks, embed them, and build the FAISS index.
        Safe to call multiple times (skips if already built, unless force=True).
        Falls back to loading metadata only when semantic deps are unavailable.
        """
        if self._built and not force:
            return

        docs = self._load_runbooks()
        if not docs:
            logger.warning("No runbooks found in", path=str(self._runbooks_dir))
            return

        # Always populate metadata so keyword search and listing work
        self._meta = docs

        try:
            embeddings = self._embed([d["body"] for d in docs])
            import faiss  # noqa: PLC0415
            dim = embeddings.shape[1]
            # Inner-product index on L2-normalised vectors = cosine similarity
            self._index = faiss.IndexFlatIP(dim)
            faiss.normalize_L2(embeddings)
            self._index.add(embeddings)
            self._semantic_available = True
            logger.info("Runbook FAISS index built", n_docs=len(docs), dim=dim)
        except Exception as exc:
            self._semantic_available = False
            logger.warning(
                "sentence-transformers or faiss-cpu unavailable — "
                "runbook search will use lexical fallback",
                error=str(exc),
            )

        self._built = True

    # ── Public search interface ────────────────────────────────────────────

    def search(self, query: str, top_k: int = 3) -> List[RunbookHit]:
        """
        Return top-k matching runbooks for a query string.
        Uses FAISS semantic search when available; falls back to TF-IDF
        lexical search otherwise.  The ``search_mode`` field on each hit
        indicates which method was used.
        """
        if not self._built:
            self.build_index()
        if not self._meta:
            return []

        if self._semantic_available:
            return self._semantic_search(query, top_k)
        return self._keyword_search(query, top_k)

    def search_detail(self, query: str, top_k: int = 3) -> List[RunbookDetail]:
        """Like search() but returns full RunbookDetail objects."""
        hits = self.search(query, top_k=top_k)
        details = []
        for hit in hits:
            doc = next((d for d in self._meta if d["slug"] == hit.slug), None)
            if doc:
                details.append(_build_runbook_detail(doc, hit.score, hit.search_mode))
        return details

    def get_runbook_detail(self, slug: str) -> Optional[RunbookDetail]:
        """Return full RunbookDetail for a specific slug, or None if not found."""
        if not self._meta:
            self._meta = self._load_runbooks()
        doc = next((d for d in self._meta if d["slug"] == slug), None)
        if doc is None:
            return None
        return _build_runbook_detail(doc, score=1.0, search_mode="exact")

    def embed_text(self, text: str) -> Optional[np.ndarray]:
        """
        Return a normalised embedding for a single text, or None when
        sentence-transformers is unavailable.
        """
        if self._semantic_available is False:
            return None
        try:
            emb = self._embed([text])
            import faiss  # noqa: PLC0415
            faiss.normalize_L2(emb)
            return emb[0]
        except Exception:
            self._semantic_available = False
            return None

    # ── Internal search implementations ───────────────────────────────────

    def _semantic_search(self, query: str, top_k: int) -> List[RunbookHit]:
        q_emb = self._embed([query])
        import faiss  # noqa: PLC0415
        faiss.normalize_L2(q_emb)

        k = min(top_k, len(self._meta))
        scores, indices = self._index.search(q_emb, k)

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
                    search_mode="semantic",
                )
            )
        return hits

    def _keyword_search(self, query: str, top_k: int) -> List[RunbookHit]:
        """
        TF-IDF / lexical keyword similarity over runbook content.
        Clearly labelled as ``search_mode: "lexical"``.
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: PLC0415
            from sklearn.metrics.pairwise import cosine_similarity  # noqa: PLC0415

            corpus = [d["body"] for d in self._meta]
            vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
            tfidf_matrix = vectorizer.fit_transform(corpus)
            q_vec = vectorizer.transform([query])
            sims = cosine_similarity(q_vec, tfidf_matrix)[0]
        except ImportError:
            # Pure-Python token-frequency lexical fallback when sklearn is not installed
            sims = self._token_lexical_similarity(query)

        top_indices = np.argsort(sims)[::-1][: min(top_k, len(self._meta))]
        hits = []
        for idx in top_indices:
            doc = self._meta[idx]
            hits.append(
                RunbookHit(
                    slug=doc["slug"],
                    title=doc["title"],
                    score=float(sims[idx]),
                    excerpt=doc["excerpt"],
                    search_mode="lexical",
                )
            )
        return hits

    def _token_lexical_similarity(self, query: str) -> np.ndarray:
        """
        Lightweight lexical similarity fallback using token overlap and weighting.
        Scores range [0.0, 1.0].
        """
        stopwords = {
            "a", "an", "the", "and", "or", "in", "on", "at", "to", "for",
            "with", "is", "was", "are", "by", "of", "from", "it", "this",
        }
        q_tokens = [
            w for w in re.findall(r"[a-z0-9_-]+", query.lower())
            if w not in stopwords and len(w) > 1
        ]
        if not q_tokens:
            return np.zeros(len(self._meta))

        scores = []
        for d in self._meta:
            title_lower = d["title"].lower()
            tags_lower = d.get("tags", "").lower()
            body_lower = d["body"].lower()
            score = 0.0
            for t in q_tokens:
                if t in title_lower:
                    score += 3.0
                if t in tags_lower:
                    score += 2.0
                score += min(body_lower.count(t) * 0.2, 2.0)
            norm_score = min(score / (len(q_tokens) * 7.0), 1.0)
            scores.append(norm_score)
        return np.array(scores, dtype=np.float32)

    # ── Helpers ────────────────────────────────────────────────────────────

    def _load_runbooks(self) -> List[dict]:
        docs = []
        for path in sorted(self._runbooks_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8", errors="replace")
            slug = path.stem

            # Parse front-matter fields
            fm_fields: dict = {}
            fm_match = re.search(r"^---\n(.*?)\n---\n", text, re.DOTALL)
            if fm_match:
                for m in _FM_FIELD_RE.finditer(fm_match.group(1)):
                    fm_fields[m.group(1).strip()] = m.group(2).strip()

            title = fm_fields.get("title", slug.replace("-", " ").title())
            runbook_id = fm_fields.get("id", slug)
            tags = fm_fields.get("tags", "")

            # Strip front-matter for body
            body = _FRONT_MATTER_RE.sub("", text).strip()
            excerpt = body[:300].replace("\n", " ")

            docs.append({
                "slug": slug,
                "id": runbook_id,
                "title": title,
                "tags": tags,
                "body": body,
                "excerpt": excerpt,
            })
        return docs

    def _embed(self, texts: List[str]) -> np.ndarray:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer  # noqa: PLC0415
            except ImportError as exc:
                raise ImportError(
                    "sentence-transformers is required. Run: pip install sentence-transformers"
                ) from exc
            model_name = _DEFAULT_EMBEDDING_MODEL
            logger.info("Loading embedding model", model=model_name)
            self._model = SentenceTransformer(model_name)
        embeddings = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.astype(np.float32)


# ── Module-level singleton ─────────────────────────────────────────────────
retrieval_service = RetrievalService()
