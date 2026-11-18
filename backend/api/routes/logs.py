"""API Routes for Log Upload and Anomaly Analysis."""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import AnalyzeRequest, AnalyzeResponse, LogUploadResponse
from backend.core.logging import get_logger
from backend.db.database import get_session
from backend.services.pipeline_service import pipeline_service

logger = get_logger(__name__)
router = APIRouter(prefix="/logs", tags=["Logs & Ingestion"])

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB limit
ALLOWED_EXTENSIONS = {".log", ".txt", ".csv"}
UPLOAD_DIR = Path("data/raw/uploads")


@router.post(
    "/upload",
    response_model=LogUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload raw log file",
    description="Validates file format and size, stages it, and returns file tracking metadata.",
)
async def upload_log_file(
    file: UploadFile = File(..., description="Log file (.log, .txt, .csv) up to 25MB"),
) -> LogUploadResponse:
    """Validate and upload raw log file."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename cannot be empty.",
        )

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    content = await file.read()
    size_bytes = len(content)

    if size_bytes > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB.",
        )

    file_id = f"file-{uuid.uuid4().hex[:8]}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    stored_path.write_bytes(content)

    lines = content.decode("utf-8", errors="replace").splitlines()
    total_lines = len([l for l in lines if l.strip()])

    logger.info("Uploaded log file", file_id=file_id, filename=file.filename, lines=total_lines, size=size_bytes)

    return LogUploadResponse(
        file_id=file_id,
        filename=file.filename,
        size_bytes=size_bytes,
        total_lines=total_lines,
        message=f"File '{file.filename}' uploaded successfully with {total_lines:,} lines.",
    )


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze log stream for anomalies",
    description="Parses logs with Drain3, extracts block features, runs Isolation Forest, and stores incidents in SQLite.",
)
async def analyze_logs(
    payload: AnalyzeRequest,
    db: AsyncSession = Depends(get_session),
) -> AnalyzeResponse:
    """End-to-end log parsing, feature extraction, anomaly detection, and incident creation."""
    lines_to_process: List[str] = []

    # 1. Process inline lines if supplied
    if payload.lines is not None:
        lines_to_process.extend(payload.lines)

    # 2. Or load from staged upload if session_id matches a file
    elif payload.session_id:
        matching_files = list(UPLOAD_DIR.glob(f"{payload.session_id}_*"))
        if matching_files:
            file_content = matching_files[0].read_text(encoding="utf-8", errors="replace")
            lines_to_process = file_content.splitlines()

    if not lines_to_process:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No log lines provided. Supply 'lines' in body or a valid 'session_id' from /upload.",
        )

    response = await pipeline_service.analyze_logs(
        lines=lines_to_process,
        session_id=payload.session_id,
        db=db,
        threshold=payload.threshold,
    )
    return response
