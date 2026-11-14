"""GET /anomalies — list detected anomalies."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_session
from backend.db.models import Anomaly

router = APIRouter()


class AnomalyOut(BaseModel):
    id: int
    log_entry_id: int
    score: float
    label: str
    detector: str
    detected_at: str

    model_config = {"from_attributes": True}


@router.get("", response_model=List[AnomalyOut], summary="List anomalies")
async def list_anomalies(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    label: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
) -> List[AnomalyOut]:
    """Return paginated list of anomaly records."""
    q = select(Anomaly).order_by(Anomaly.detected_at.desc()).offset(offset).limit(limit)
    if label:
        q = q.where(Anomaly.label == label)
    result = await session.execute(q)
    rows = result.scalars().all()
    return [
        AnomalyOut(
            id=r.id,
            log_entry_id=r.log_entry_id,
            score=r.score,
            label=r.label,
            detector=r.detector,
            detected_at=r.detected_at.isoformat(),
        )
        for r in rows
    ]
