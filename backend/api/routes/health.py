"""GET /health — liveness & readiness probe."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_session

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    database: str
    version: str = "0.1.0"


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check(session: AsyncSession = Depends(get_session)) -> HealthResponse:
    """Returns service liveness and DB connectivity."""
    db_status = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat(),
        database=db_status,
    )
