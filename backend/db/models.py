"""SQLAlchemy ORM models for LogSage Backend."""
from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IncidentSeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class IncidentStatus(str, enum.Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"


# ── LogEntry ───────────────────────────────────────────────────────────────

class LogEntry(Base):
    __tablename__ = "log_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    block_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    line_number: Mapped[int] = mapped_column(Integer, default=0)
    raw_line: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    level: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    component: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    event_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    event_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parameters_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<LogEntry id={self.id} block_id={self.block_id!r} event_id={self.event_id!r}>"


# ── Incident ───────────────────────────────────────────────────────────────

class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    block_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    severity: Mapped[str] = mapped_column(
        Enum(IncidentSeverity), nullable=False, default=IncidentSeverity.MEDIUM, index=True
    )
    status: Mapped[str] = mapped_column(
        Enum(IncidentStatus), nullable=False, default=IncidentStatus.OPEN, index=True
    )
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False)
    event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    top_features_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_evidence_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    def __init__(self, *args, session_id: Optional[str] = None, **kwargs):
        super().__init__(*args, **kwargs)
        # Note: session_id is a transient in-memory annotation used during the active
        # ingestion transaction; it is not a persisted database column. Reloaded or
        # query-fetched incidents rely on database LogEntry provenance resolution.
        self.session_id = session_id

    def __repr__(self) -> str:
        return f"<Incident {self.incident_id} block_id={self.block_id} score={self.anomaly_score:.3f}>"


# ── RunbookRecord ──────────────────────────────────────────────────────────

class RunbookRecord(Base):
    __tablename__ = "runbooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    indexed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<RunbookRecord slug={self.slug!r}>"
