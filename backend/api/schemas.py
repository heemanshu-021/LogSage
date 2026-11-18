"""Pydantic request and response schemas for LogSage API."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Health ─────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall health status")
    timestamp: str = Field(..., description="Current ISO-8601 timestamp")
    database: str = Field(..., description="Database connectivity status: 'ok' or 'error'")
    ml_model_loaded: bool = Field(..., description="Whether the ML anomaly detector is loaded")
    version: str = Field("0.1.0", description="API version")


# ── Log Upload ─────────────────────────────────────────────────────────────

class LogUploadResponse(BaseModel):
    file_id: str = Field(..., description="Generated file tracking ID")
    filename: str = Field(..., description="Original uploaded filename")
    size_bytes: int = Field(..., description="File size in bytes")
    total_lines: int = Field(..., description="Total line count in the file")
    message: str = Field(..., description="Status summary message")


# ── Log Analysis ───────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    lines: Optional[List[str]] = Field(None, description="Raw log lines to analyze")
    session_id: Optional[str] = Field(None, description="Optional session or file identifier")
    threshold: Optional[float] = Field(None, description="Custom anomaly score threshold [0.0 - 1.0]")


class FeatureAttribution(BaseModel):
    feature: str = Field(..., description="Feature name")
    value: float = Field(..., description="Normalized feature value")


class IncidentSummary(BaseModel):
    incident_id: str = Field(..., description="Unique incident identifier, e.g. INC-0001")
    block_id: str = Field(..., description="Target HDFS Block ID")
    title: str = Field(..., description="Summary title of the incident")
    severity: str = Field(..., description="Severity level: CRITICAL, HIGH, MEDIUM, LOW")
    status: str = Field(..., description="Incident status: OPEN, INVESTIGATING, RESOLVED")
    anomaly_score: float = Field(..., description="Continuous anomaly score [0.0 - 1.0]")
    event_count: int = Field(..., description="Total log events associated with this block")
    created_at: str = Field(..., description="Incident timestamp")


class AnalyzeResponse(BaseModel):
    session_id: str = Field(..., description="Analysis session ID")
    total_lines: int = Field(..., description="Total log lines processed")
    total_blocks: int = Field(..., description="Total unique blocks identified")
    anomalous_blocks: int = Field(..., description="Total anomalous blocks flagged")
    incidents_created: int = Field(..., description="Number of new incident records persisted")
    processing_time_ms: float = Field(..., description="Pipeline execution latency in milliseconds")
    incidents: List[IncidentSummary] = Field(default_factory=list, description="List of generated incidents")


# ── Incidents ──────────────────────────────────────────────────────────────

class IncidentDetail(BaseModel):
    incident_id: str
    block_id: str
    title: str
    severity: str
    status: str
    anomaly_score: float
    event_count: int
    top_features: List[FeatureAttribution]
    raw_evidence: List[str]
    recommended_runbooks: List[Dict[str, Any]]
    created_at: str
    updated_at: str


class IncidentListResponse(BaseModel):
    total: int = Field(..., description="Total matching incidents")
    limit: int = Field(..., description="Page size limit")
    offset: int = Field(..., description="Page offset")
    incidents: List[IncidentSummary] = Field(default_factory=list)


# ── Dashboard Metrics ──────────────────────────────────────────────────────

class DashboardMetrics(BaseModel):
    total_logs_ingested: int = Field(..., description="Cumulative log entries recorded")
    total_blocks_analyzed: int = Field(..., description="Total unique blocks evaluated")
    total_incidents: int = Field(..., description="Total incidents ever recorded")
    open_incidents: int = Field(..., description="Number of currently open incidents")
    anomaly_rate_percent: float = Field(..., description="Percentage of blocks flagged as anomalous")
    severity_breakdown: Dict[str, int] = Field(..., description="Counts per severity level")
    status_breakdown: Dict[str, int] = Field(..., description="Counts per status level")
    recent_incidents: List[IncidentSummary] = Field(default_factory=list, description="Latest incidents")
