"""Custom exception hierarchy for LogSage."""
from __future__ import annotations

from fastapi import HTTPException, status


class LogSageError(Exception):
    """Base exception for all LogSage domain errors."""

    def __init__(self, message: str, detail: str | None = None):
        super().__init__(message)
        self.message = message
        self.detail = detail or message


# ── Parsing ────────────────────────────────────────────────────────────────

class LogParseError(LogSageError):
    """Raised when a log line cannot be parsed."""


# ── ML ─────────────────────────────────────────────────────────────────────

class ModelNotTrainedError(LogSageError):
    """Raised when predict() is called before fit()."""


class FeatureExtractionError(LogSageError):
    """Raised when feature extraction fails."""


# ── Retrieval ──────────────────────────────────────────────────────────────

class RunbookIndexError(LogSageError):
    """Raised when the FAISS runbook index is not built."""


class RunbookNotFoundError(LogSageError):
    """Raised when no matching runbook is found."""


# ── API helpers ────────────────────────────────────────────────────────────

def raise_404(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def raise_422(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


def raise_500(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
