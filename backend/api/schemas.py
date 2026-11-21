"""Pydantic request and response schemas for LogSage API."""
from __future__ import annotations

from datetime import datetime
import math
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


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


# ── Runbook Retrieval ──────────────────────────────────────────────────────

class RunbookHitOut(BaseModel):
    """Lightweight runbook hit returned by /runbooks/search."""
    slug: str = Field(..., description="Runbook filename without extension")
    title: str = Field(..., description="Runbook title")
    score: float = Field(..., description="Similarity score [0, 1]")
    excerpt: str = Field(..., description="First 300 characters of runbook body")
    search_mode: str = Field("semantic", description="'semantic' or 'lexical'")


class RunbookDetailOut(BaseModel):
    """Full runbook content returned by GET /api/incidents/{id}/runbooks."""
    slug: str
    id: str = Field(..., description="Runbook unique ID (e.g. RB-001)")
    title: str
    score: float = Field(..., description="Similarity score [0, 1]")
    search_mode: str = Field(..., description="'semantic' or 'lexical'")
    tags: List[str] = Field(default_factory=list)
    symptoms: str = Field("", description="Symptoms section from runbook")
    possible_causes: str = Field("", description="Possible causes section")
    investigation_steps: str = Field("", description="Investigation / triage steps")
    remediation: str = Field("", description="Remediation instructions")
    verification_steps: str = Field("", description="Post-fix verification steps")
    escalation: str = Field("", description="Escalation guidance")


class IncidentRunbooksResponse(BaseModel):
    """Response for GET /api/incidents/{incident_id}/runbooks."""
    incident_id: str
    query_text: str = Field(..., description="The incident description used as the search query")
    search_mode: str = Field(..., description="'semantic' or 'lexical'")
    runbooks: List[RunbookDetailOut] = Field(default_factory=list)


# ── Similar Incidents ──────────────────────────────────────────────────────

class SimilarIncidentResult(BaseModel):
    """One entry in a similar-incident list."""
    incident_id: str
    block_id: str
    title: str
    severity: str
    status: str
    anomaly_score: float
    similarity_score: float = Field(..., description="Cosine similarity [0, 1] or keyword score")
    search_mode: str = Field(..., description="'semantic' or 'lexical'")
    created_at: str


class SimilarIncidentsResponse(BaseModel):
    """Response for GET /api/incidents/{incident_id}/similar."""
    incident_id: str
    query_text: str = Field(..., description="The context/description used as the similarity query")
    search_mode: str
    similar_incidents: List[SimilarIncidentResult] = Field(default_factory=list)


# ── Incident Update ────────────────────────────────────────────────────────

class IncidentUpdateRequest(BaseModel):
    """Request body for PATCH /api/incidents/{incident_id}."""
    status: str = Field(..., description="New status: OPEN, INVESTIGATING, RESOLVED")
    notes: Optional[str] = Field(None, description="Optional operator triage notes")


# ── AI Incident Triage Engine ──────────────────────────────────────────────

class TriageSimilarIncident(BaseModel):
    """Reference to a similar historical incident within a triage report."""
    incident_id: str
    title: str
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity [0, 1] or keyword score")
    search_mode: Literal["semantic", "lexical"] = Field(..., description="'semantic' or 'lexical'")
    severity: Optional[str] = None
    status: Optional[str] = None

    @field_validator("similarity_score")
    @classmethod
    def validate_finite_similarity(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("similarity_score must be a finite number between 0 and 1")
        return v


class TriageRunbookReference(BaseModel):
    """Reference to a troubleshooting runbook within a triage report."""
    slug: str
    id: str
    title: str
    score: float = Field(..., ge=0.0, le=1.0, description="Runbook relevance score [0, 1]")
    search_mode: Literal["semantic", "lexical"] = Field(..., description="'semantic' or 'lexical'")
    symptoms: Optional[str] = ""
    remediation: Optional[str] = ""

    @field_validator("score")
    @classmethod
    def validate_finite_score(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("score must be a finite number between 0 and 1")
        return v


class IncidentTriageReport(BaseModel):
    """Comprehensive, evidence-grounded AI Incident Triage Report."""
    incident_id: str = Field(..., description="Target incident ID")
    block_id: str = Field(..., description="Associated block or cluster ID")
    title: str = Field(..., description="Incident title")
    executive_summary: str = Field(..., description="Executive summary of the incident")
    estimated_severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = Field(..., description="Estimated severity: CRITICAL, HIGH, MEDIUM, LOW")
    observed_symptoms: List[str] = Field(default_factory=list, description="Observed symptoms directly grounded in log evidence")
    original_log_evidence: List[str] = Field(default_factory=list, description="Original raw log lines from incident record")
    possible_root_causes: List[str] = Field(default_factory=list, description="Possible root-cause hypotheses clearly distinguished from facts")
    similar_historical_incidents: List[TriageSimilarIncident] = Field(default_factory=list, description="Relevant similar historical incidents")
    relevant_runbooks: List[TriageRunbookReference] = Field(default_factory=list, description="Relevant troubleshooting runbooks")
    recommended_investigation_steps: List[str] = Field(default_factory=list, description="Actionable investigation steps derived from runbooks and evidence")
    suggested_remediation: List[str] = Field(default_factory=list, description="Actionable remediation steps from runbooks")
    confidence_level: Literal["HIGH", "MEDIUM", "LOW"] = Field(..., description="Confidence level: HIGH, MEDIUM, or LOW")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Numerical confidence score [0, 1]")
    uncertainty_and_missing_information: str = Field(..., description="Explicit description of uncertainty, gaps, and missing context")
    generation_mode: Literal["llm", "retrieval_fallback"] = Field(..., description="Generation mode: 'llm' or 'retrieval_fallback'")
    model_name: Optional[str] = Field(None, description="LLM model name if generation_mode is 'llm'")
    generated_at: str = Field(..., description="ISO-8601 generation timestamp")

    @field_validator("confidence_score")
    @classmethod
    def validate_finite_confidence(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("confidence_score must be a finite number between 0 and 1")
        return v
