"""API Routes for Incident Management."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import IncidentDetail, IncidentListResponse
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
