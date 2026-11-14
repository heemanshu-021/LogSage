"""POST /logs/ingest — receive raw log lines for parsing and detection."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_session
from backend.services.ingest import ingest_and_detect
from backend.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class IngestRequest(BaseModel):
    lines: List[str]
    source: str = "api"
    session_id: str | None = None


class IngestResponse(BaseModel):
    accepted: int
    anomalies_detected: int
    session_id: str | None
    message: str


@router.post("/ingest", response_model=IngestResponse, summary="Ingest log lines")
async def ingest_logs(
    payload: IngestRequest,
    db: AsyncSession = Depends(get_session),
) -> IngestResponse:
    """Accept a batch of raw log lines, parse, detect anomalies."""
    if not payload.lines:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="lines must be non-empty",
        )

    n_ingested, n_anomalies = await ingest_and_detect(
        lines=payload.lines,
        source=payload.source,
        session_id=payload.session_id,
        db=db,
    )

    return IngestResponse(
        accepted=n_ingested,
        anomalies_detected=n_anomalies,
        session_id=payload.session_id,
        message=f"Ingested {n_ingested} lines, detected {n_anomalies} anomalies.",
    )


@router.post("/ingest/file", response_model=IngestResponse, summary="Upload a log file")
async def ingest_file(
    file: UploadFile = File(...),
    source: str = "api",
    db: AsyncSession = Depends(get_session),
) -> IngestResponse:
    """Upload a .log / .txt file; each line is ingested."""
    content = await file.read()
    lines = content.decode("utf-8", errors="replace").splitlines()
    return await ingest_logs(
        IngestRequest(lines=lines, source=source, session_id=file.filename),
        db=db,
    )
