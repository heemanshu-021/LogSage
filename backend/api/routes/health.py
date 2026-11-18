"""GET /health and GET /api/health — liveness, database, and ML model probe."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import HealthResponse
from backend.db.database import get_session
from backend.services.pipeline_service import pipeline_service

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="System health check")
async def health_check(session: AsyncSession = Depends(get_session)) -> HealthResponse:
    """Returns service liveness, database status, and ML model readiness."""
    db_status = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat(),
        database=db_status,
        ml_model_loaded=pipeline_service.is_ml_ready,
        version="0.1.0",
    )
