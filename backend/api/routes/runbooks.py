"""GET /runbooks/search — semantic runbook retrieval (Phase 5 complete)."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Query
from pydantic import BaseModel

from backend.services.retrieval import retrieval_service

router = APIRouter()


class RunbookHitOut(BaseModel):
    slug: str
    title: str
    score: float
    excerpt: str


@router.get("/search", response_model=List[RunbookHitOut], summary="Search runbooks")
async def search_runbooks(
    q: str = Query(..., min_length=3, description="Query / anomaly description"),
    top_k: int = Query(3, ge=1, le=10),
) -> List[RunbookHitOut]:
    """Return top-k runbooks semantically relevant to the query."""
    try:
        hits = retrieval_service.search(q, top_k=top_k)
    except ImportError:
        # Gracefully handle absent optional dependencies (sentence-transformers / faiss-cpu)
        hits = []
    return [
        RunbookHitOut(slug=h.slug, title=h.title, score=h.score, excerpt=h.excerpt)
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
