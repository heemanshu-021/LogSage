"""API Routes for Log Upload and Anomaly Analysis."""
from __future__ import annotations

import os
import time
import uuid
from io import StringIO
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import (
    MAX_ANALYZE_LINES,
    MAX_LOG_LINE_CHARS,
    AnalyzeRequest,
    AnalyzeResponse,
    LogUploadResponse,
)
from backend.core.logging import get_logger
from backend.db.database import get_session
from backend.services.pipeline_service import pipeline_service

logger = get_logger(__name__)
router = APIRouter(prefix="/logs", tags=["Logs & Ingestion"])

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB limit
STAGED_UPLOAD_TTL_SECONDS = 24 * 60 * 60
ALLOWED_EXTENSIONS = {".log", ".txt", ".csv"}
UPLOAD_DIR = Path(os.environ.get("LOGSAGE_UPLOAD_DIR", "data/raw/uploads"))


def cleanup_expired_uploads(
    directory: Path = UPLOAD_DIR,
    *,
    now: float | None = None,
    ttl_seconds: int = STAGED_UPLOAD_TTL_SECONDS,
) -> int:
    """Remove expired staged LogSage uploads; return the number removed."""
    current_time = time.time() if now is None else now
    cutoff = current_time - ttl_seconds
    removed = 0
    if not directory.exists():
        return removed
    try:
        for path in directory.iterdir():
            if (
                path.is_symlink()
                or not path.is_file()
                or not path.name.startswith("file-")
                or "_" not in path.name[5:]
            ):
                continue
            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink()
                    removed += 1
            except OSError as exc:
                logger.warning("Could not remove expired staged upload", path=str(path), error=str(exc))
    except OSError as exc:
        logger.warning("Could not inspect staged upload directory", path=str(directory), error=str(exc))
    return removed


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

    # Read at most one byte beyond the limit so an oversized upload cannot be
    # fully buffered in memory before it is rejected.
    content = await file.read(MAX_FILE_SIZE_BYTES + 1)
    size_bytes = len(content)

    if size_bytes > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB.",
        )

    decoded_content = content.decode("utf-8", errors="replace")
    physical_lines = 0
    total_lines = 0
    for line in StringIO(decoded_content):
        physical_lines += 1
        if physical_lines > MAX_ANALYZE_LINES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds the {MAX_ANALYZE_LINES:,}-line analysis limit.",
            )
        if len(line.rstrip("\r\n")) > MAX_LOG_LINE_CHARS:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"A log line exceeds the {MAX_LOG_LINE_CHARS:,}-character limit.",
            )
        if line.strip():
            total_lines += 1

    file_id = f"file-{uuid.uuid4().hex}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_filename = Path(file.filename.replace("\\", "/")).name
    stored_path = UPLOAD_DIR / f"{file_id}_{safe_filename}"
    stored_path.write_bytes(content)

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
            lines_to_process = [line for line in file_content.splitlines() if line.strip()]

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
