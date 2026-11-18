"""API Routes for Incident Management."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import (
    IncidentDetail,
    IncidentListResponse,
    IncidentRunbooksResponse,
    SimilarIncidentsResponse,
)
from backend.core.logging import get_logger
from backend.db.database import get_session
from backend.services.pipeline_service import pipeline_service

logger = get_logger(__name__)
router = APIRouter(prefix="/incidents", tags=["Incidents & Triage"])


@router.get(
    "",
    response_model=IncidentListResponse,
    summary="List detected incidents",
    description="Returns paginated incident records with optional severity and status filtering.",
)
async def list_incidents(
    limit: int = Query(50, ge=1, le=500, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    severity: Optional[str] = Query(None, description="Filter by severity: CRITICAL, HIGH, MEDIUM, LOW"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: OPEN, INVESTIGATING, RESOLVED"),
    db: AsyncSession = Depends(get_session),
) -> IncidentListResponse:
    """Retrieve list of flagged incidents."""
    incidents, total = await pipeline_service.list_incidents(
        db=db,
        limit=limit,
        offset=offset,
        severity=severity,
        status=status_filter,
    )
    return IncidentListResponse(
        total=total,
        limit=limit,
        offset=offset,
        incidents=incidents,
    )


# ── Sub-routes registered BEFORE /{incident_id} wildcard ──────────────────
# FastAPI matches routes in declaration order. Static paths like /similar
# and /runbooks must come before the /{incident_id} dynamic segment.


@router.get(
    "/{incident_id}/similar",
    response_model=SimilarIncidentsResponse,
    summary="Find similar historical incidents",
    description=(
        "Retrieves the top-k incidents whose titles are most similar to the given incident. "
        "Uses semantic (cosine) similarity when sentence-transformers is available; "
        "falls back to TF-IDF lexical similarity otherwise. "
        "The current incident is excluded from results."
    ),
)
async def get_similar_incidents(
    incident_id: str,
    top_k: int = Query(5, ge=1, le=20, description="Maximum number of similar incidents to return"),
    db: AsyncSession = Depends(get_session),
) -> SimilarIncidentsResponse:
    """Return incidents most similar to the given incident."""
    result = await pipeline_service.get_similar_incidents(
        incident_id=incident_id,
        db=db,
        top_k=top_k,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )
    return SimilarIncidentsResponse(**result)


@router.get(
    "/{incident_id}/runbooks",
    response_model=IncidentRunbooksResponse,
    summary="Get relevant runbooks for an incident",
    description=(
        "Retrieves up to 3 runbooks most relevant to the incident description. "
        "Uses semantic similarity when sentence-transformers is available; "
        "falls back to TF-IDF lexical search otherwise. "
        "The search_mode field in the response indicates which method was used."
    ),
)
async def get_incident_runbooks(
    incident_id: str,
    top_k: int = Query(3, ge=1, le=10, description="Maximum number of runbooks to return"),
    db: AsyncSession = Depends(get_session),
) -> IncidentRunbooksResponse:
    """Return relevant runbooks for the given incident."""
    result = await pipeline_service.get_incident_runbooks(
        incident_id=incident_id,
        db=db,
        top_k=top_k,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )
    return IncidentRunbooksResponse(**result)


@router.get(
    "/{incident_id}",
    response_model=IncidentDetail,
    summary="Get incident details",
    description="Returns complete incident evidence, anomaly attribution features, and recommended triage runbooks.",
)
async def get_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_session),
) -> IncidentDetail:
    """Fetch individual incident record by incident ID."""
    detail = await pipeline_service.get_incident(incident_id=incident_id, db=db)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID '{incident_id}' not found.",
        )
    return detail
