"""API Routes for Operational Dashboard Metrics."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import DashboardMetrics
from backend.core.logging import get_logger
from backend.db.database import get_session
from backend.services.pipeline_service import pipeline_service

logger = get_logger(__name__)
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/metrics",
    response_model=DashboardMetrics,
    summary="Get operational dashboard metrics",
    description="Aggregates system-wide counts: total logs ingested, unique blocks analyzed, open incidents, and severity breakdowns.",
)
async def get_dashboard_metrics(
    db: AsyncSession = Depends(get_session),
) -> DashboardMetrics:
    """Return live system metrics."""
    return await pipeline_service.get_dashboard_metrics(db=db)
