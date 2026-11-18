"""GET /runbooks — semantic runbook listing and search."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Query

from backend.api.schemas import RunbookHitOut
from backend.services.retrieval import retrieval_service

router = APIRouter()


@router.get("/search", response_model=List[RunbookHitOut], summary="Search runbooks")
async def search_runbooks(
    q: str = Query(..., min_length=3, description="Query / anomaly description"),
    top_k: int = Query(3, ge=1, le=10),
) -> List[RunbookHitOut]:
    """
    Return top-k runbooks semantically relevant to the query.

    Uses FAISS semantic search when sentence-transformers and faiss-cpu are
    installed; falls back to TF-IDF lexical search otherwise.  The
    ``search_mode`` field on each result indicates which method was used.
    """
    try:
        hits = retrieval_service.search(q, top_k=top_k)
    except ImportError:
        # Gracefully handle absent optional dependencies (sentence-transformers / faiss-cpu)
        hits = []
    return [
        RunbookHitOut(
            slug=h.slug,
            title=h.title,
            score=h.score,
            excerpt=h.excerpt,
            search_mode=h.search_mode,
        )
        for h in hits
    ]


@router.get("", response_model=List[dict], summary="List all indexed runbooks")
async def list_runbooks() -> List[dict]:
    """Return metadata for all indexed runbooks."""
    meta = retrieval_service._meta
    if not meta:
        meta = retrieval_service._load_runbooks()
    return [
        {"slug": m["slug"], "title": m["title"], "excerpt": m["excerpt"]}
        for m in meta
    ]
