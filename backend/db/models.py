"""ORM models for LogSage."""
from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LogSource(str, enum.Enum):
    HDFS = "hdfs"
    SYSLOG = "syslog"
    CUSTOM = "custom"
    API = "api"


class AnomalyLabel(str, enum.Enum):
    NORMAL = "normal"
    ANOMALY = "anomaly"
    UNKNOWN = "unknown"


# ── LogEntry ───────────────────────────────────────────────────────────────

class LogEntry(Base):
    __tablename__ = "log_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    raw_line: Mapped[str] = mapped_column(Text, nullable=False)
    template: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    source: Mapped[str] = mapped_column(
        Enum(LogSource), nullable=False, default=LogSource.API
    )
    session_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    anomalies: Mapped[list["Anomaly"]] = relationship(
        back_populates="log_entry", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<LogEntry id={self.id} template_id={self.template_id!r}>"


# ── Anomaly ────────────────────────────────────────────────────────────────

class Anomaly(Base):
    __tablename__ = "anomalies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    log_entry_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("log_entries.id", ondelete="CASCADE"), nullable=False
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    label: Mapped[str] = mapped_column(
        Enum(AnomalyLabel), nullable=False, default=AnomalyLabel.ANOMALY
    )
    detector: Mapped[str] = mapped_column(String(64), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    log_entry: Mapped["LogEntry"] = relationship(back_populates="anomalies")

    def __repr__(self) -> str:
        return f"<Anomaly id={self.id} score={self.score:.3f} label={self.label}>"


# ── Runbook (index metadata) ───────────────────────────────────────────────

class RunbookRecord(Base):
    __tablename__ = "runbooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)   # CSV
    indexed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<RunbookRecord slug={self.slug!r}>"
