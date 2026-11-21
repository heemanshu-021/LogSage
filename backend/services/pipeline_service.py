"""
LogSage Pipeline Service — End-to-End Orchestrator.

Integrates:
- Drain3 Parsing Engine (ml.parser.drain_parser)
- Block-Level Feature Extractor (ml.preprocessing.feature_extraction)
- Isolation Forest Anomaly Detector (ml.models.isolation_forest)
- Incident Storage and Runbook Triage
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import (
    AnalyzeResponse,
    DashboardMetrics,
    FeatureAttribution,
    IncidentDetail,
    IncidentSummary,
)
from backend.core.config import settings
from backend.core.logging import get_logger
from backend.db.models import Incident, IncidentSeverity, IncidentStatus, LogEntry
from backend.services.retrieval import build_incident_context, retrieval_service
from ml.models.isolation_forest import IsolationForestDetector
from ml.parser.drain_parser import DrainParser, ParseResult
from ml.preprocessing.feature_extraction import BlockFeatureExtractor

logger = get_logger(__name__)


class PipelineService:
    """Singleton service orchestrating log parsing, ML detection, and persistence."""

    def __init__(self):
        self.parser: Optional[DrainParser] = None
        self.parser_state_loaded = False
        self.extractor: Optional[BlockFeatureExtractor] = None
        self.detector: Optional[IsolationForestDetector] = None
        self._initialise()

    def _initialise(self) -> None:
        """Load parser config and trained ML artifacts."""
        model_dir = Path(settings.MODEL_SAVE_DIR)
        try:
            config_ini = Path("ml/parser/parser_config.ini")
            parser_snapshot = model_dir / "drain_state.json"
            if parser_snapshot.exists():
                self.parser = DrainParser.load(
                    parser_snapshot,
                    config_path=config_ini if config_ini.exists() else None,
                )
                native_parser_state = parser_snapshot.with_suffix(".bin")
                self.parser_state_loaded = native_parser_state.is_file()
                if self.parser_state_loaded:
                    logger.info("Loaded trained Drain3 parser state", path=str(native_parser_state))
                else:
                    logger.warning(
                        "Drain3 native parser state is missing; model readiness is disabled",
                        path=str(native_parser_state),
                    )
            else:
                self.parser = DrainParser(config_path=config_ini if config_ini.exists() else None)
        except Exception as e:
            logger.warning("DrainParser initialisation fallback", error=str(e))
            self.parser = DrainParser()

        model_path = model_dir / "isolation_forest.joblib"
        extractor_path = model_dir / "feature_extractor.json"

        if model_path.exists() and extractor_path.exists():
            try:
                self.detector = IsolationForestDetector.load(model_path)
                self.extractor = BlockFeatureExtractor.load(extractor_path)
                logger.info("Loaded trained ML pipeline artifacts from disk")
            except Exception as exc:
                logger.error("Failed to load ML artifacts", error=str(exc))
        else:
            logger.warning("Trained ML model or extractor not found on disk yet. Running in fallback mode.")

    @property
    def is_ml_ready(self) -> bool:
        return (self.parser_state_loaded and
                self.detector is not None and self.detector.is_fitted and
                self.extractor is not None and self.extractor.is_fitted)

    def _determine_severity(
        self,
        score: float,
        has_error: bool,
        has_critical: bool = False,
    ) -> IncidentSeverity:
        if score >= 0.85 or has_critical:
            return IncidentSeverity.CRITICAL
        elif score >= 0.65 or has_error:
            return IncidentSeverity.HIGH
        elif score >= 0.45:
            return IncidentSeverity.MEDIUM
        return IncidentSeverity.LOW

    # ── Pipeline Execution ─────────────────────────────────────────────────

    async def analyze_logs(
        self,
        lines: List[str],
        session_id: Optional[str],
        db: AsyncSession,
        threshold: Optional[float] = None,
    ) -> AnalyzeResponse:
        """
        Full End-to-End Pipeline:
        1. Parse lines with Drain3
        2. Persist parsed log entries to SQLite
        3. Group events into Block IDs
        4. Extract ML feature representations
        5. Run Isolation Forest anomaly detection
        6. Create Incident records with evidence
        7. Commit to SQLite and return structured response
        """
        start_time = time.perf_counter()
        session_uuid = session_id or f"sess-{uuid.uuid4().hex[:8]}"

        if not lines:
            return AnalyzeResponse(
                session_id=session_uuid,
                total_lines=0,
                total_blocks=0,
                anomalous_blocks=0,
                incidents_created=0,
                processing_time_ms=0.0,
                incidents=[],
            )

        # 1. Parse lines using Drain3
        parsed_results: List[ParseResult] = self.parser.parse_lines(lines, update_model=True)

        # 2. Persist LogEntry records
        db_entries: List[LogEntry] = []
        for pr in parsed_results:
            b_id = pr.block_id or (pr.block_ids[0] if pr.block_ids else None)
            db_entries.append(
                LogEntry(
                    session_id=session_uuid,
                    block_id=b_id,
                    line_number=pr.line_id,
                    raw_line=pr.raw_message,
                    timestamp=pr.timestamp,
                    level=pr.level,
                    component=pr.component,
                    event_id=pr.event_id,
                    event_template=pr.event_template,
                    parameters_json=json.dumps(pr.parameters),
                )
            )

        db.add_all(db_entries)
        await db.flush()

        # 3. Group parsed events by Block ID
        event_dicts = [pr.to_dict() for pr in parsed_results]
        block_dict = BlockFeatureExtractor.group_events_by_block(event_dicts)
        total_blocks = len(block_dict)

        incidents_created: List[IncidentSummary] = []
        anomalous_blocks_count = 0

        # 4. ML Feature Extraction and Anomaly Scoring
        if total_blocks > 0 and self.is_ml_ready:
            X, b_ids = self.extractor.transform(block_dict)
            scores = self.detector.score(X)
            preds = self.detector.predict(X, threshold=threshold)

            for idx, (b_id, score, is_anom) in enumerate(zip(b_ids, scores, preds)):
                if is_anom == 1:
                    anomalous_blocks_count += 1
                    block_events_list = block_dict[b_id]
                    has_err = any(e.get("level") in ("ERROR", "CRITICAL", "FATAL") for e in block_events_list)
                    severity = self._determine_severity(float(score), has_err)

                    # Determine top contributing features
                    feature_vector = X[idx]
                    top_features = []
                    if self.extractor.feature_names_:
                        sorted_idx = np.argsort(np.abs(feature_vector))[::-1][:5]
                        for f_i in sorted_idx:
                            top_features.append({
                                "feature": self.extractor.feature_names_[f_i],
                                "value": round(float(feature_vector[f_i]), 4),
                            })

                    # Collect evidence log lines
                    evidence = [e.get("raw_message", "") for e in block_events_list[:10]]

                    inc_id = f"INC-{uuid.uuid4().hex[:6].upper()}"
                    title = f"Anomalous Block Activity on {b_id}"

                    incident_obj = Incident(
                        incident_id=inc_id,
                        block_id=b_id,
                        title=title,
                        severity=severity,
                        status=IncidentStatus.OPEN,
                        anomaly_score=round(float(score), 4),
                        event_count=len(block_events_list),
                        top_features_json=json.dumps(top_features),
                        raw_evidence_json=json.dumps(evidence),
                        session_id=session_uuid,
                    )
                    db.add(incident_obj)
                    await db.flush()

                    incidents_created.append(
                        IncidentSummary(
                            incident_id=inc_id,
                            block_id=b_id,
                            title=title,
                            severity=severity.value,
                            status=IncidentStatus.OPEN.value,
                            anomaly_score=round(float(score), 4),
                            event_count=len(block_events_list),
                            created_at=incident_obj.created_at.isoformat(),
                        )
                    )

        elif total_blocks > 0 and not self.is_ml_ready:
            # Fallback heuristic detector when ML artifacts are not fitted yet
            logger.info("Running heuristic anomaly detection in fallback mode (ML model not loaded)")
            extractor = self.extractor or BlockFeatureExtractor(scale_features=False)
            effective_th = threshold if threshold is not None else 0.5

            for b_id, block_events_list in block_dict.items():
                bf = extractor._extract_single_block_features(b_id, block_events_list)
                has_critical = any(str(e.get("level") or "").upper() in ("CRITICAL", "FATAL") for e in block_events_list)
                has_err = (bf.has_error > 0 or has_critical)

                if has_critical:
                    score = min(1.0, 0.90 + 0.05 * bf.error_count)
                elif bf.error_count > 0:
                    score = min(0.90, 0.70 + 0.05 * bf.error_count)
                elif bf.warn_count > 0:
                    score = min(0.60, 0.40 + 0.05 * bf.warn_count)
                else:
                    score = 0.10

                is_anom = 1 if score >= effective_th else 0

                if is_anom == 1:
                    anomalous_blocks_count += 1
                    severity = self._determine_severity(float(score), has_err, has_critical)

                    top_features = [
                        {"feature": "error_count", "value": float(bf.error_count)},
                        {"feature": "has_error", "value": float(bf.has_error)},
                        {"feature": "warn_count", "value": float(bf.warn_count)},
                        {"feature": "total_events", "value": float(bf.total_events)},
                        {"feature": "event_entropy", "value": round(float(bf.event_entropy), 4)},
                    ]

                    evidence = [e.get("raw_message", "") for e in block_events_list[:10]]
                    inc_id = f"INC-{uuid.uuid4().hex[:6].upper()}"
                    title = f"Anomalous Block Activity on {b_id}"

                    incident_obj = Incident(
                        incident_id=inc_id,
                        block_id=b_id,
                        title=title,
                        severity=severity,
                        status=IncidentStatus.OPEN,
                        anomaly_score=round(float(score), 4),
                        event_count=len(block_events_list),
                        top_features_json=json.dumps(top_features),
                        raw_evidence_json=json.dumps(evidence),
                        session_id=session_uuid,
                    )
                    db.add(incident_obj)
                    await db.flush()

                    incidents_created.append(
                        IncidentSummary(
                            incident_id=inc_id,
                            block_id=b_id,
                            title=title,
                            severity=severity.value,
                            status=IncidentStatus.OPEN.value,
                            anomaly_score=round(float(score), 4),
                            event_count=len(block_events_list),
                            created_at=incident_obj.created_at.isoformat(),
                        )
                    )

        await db.commit()

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            "Analyzed log stream",
            lines=len(lines),
            blocks=total_blocks,
            anomalies=anomalous_blocks_count,
            latency_ms=round(latency_ms, 2),
        )

        return AnalyzeResponse(
            session_id=session_uuid,
            total_lines=len(lines),
            total_blocks=total_blocks,
            anomalous_blocks=anomalous_blocks_count,
            incidents_created=len(incidents_created),
            processing_time_ms=round(latency_ms, 2),
            incidents=incidents_created,
        )

    # ── Incidents Retrieval ────────────────────────────────────────────────

    async def list_incidents(
        self,
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        severity: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Tuple[List[IncidentSummary], int]:
        """Fetch paginated incidents."""
        q = select(Incident)
        if severity:
            q = q.where(Incident.severity == severity.upper())
        if status:
            q = q.where(Incident.status == status.upper())

        # Total count
        count_q = select(func.count()).select_from(q.subquery())
        total_res = await db.execute(count_q)
        total = total_res.scalar_one()

        # Paginated rows
        q = q.order_by(Incident.created_at.desc()).offset(offset).limit(limit)
        res = await db.execute(q)
        rows = res.scalars().all()

        summaries = [
            IncidentSummary(
                incident_id=r.incident_id,
                block_id=r.block_id,
                title=r.title,
                severity=r.severity,
                status=r.status,
                anomaly_score=r.anomaly_score,
                event_count=r.event_count,
                created_at=r.created_at.isoformat(),
            )
            for r in rows
        ]
        return summaries, total

    async def get_incident(
        self,
        incident_id: str,
        db: AsyncSession,
    ) -> Optional[IncidentDetail]:
        """Fetch full incident detail with evidence and recommended runbooks."""
        q = select(Incident).where(Incident.incident_id == incident_id)
        res = await db.execute(q)
        inc = res.scalars().first()
        if not inc:
            return None

        top_features = []
        if inc.top_features_json:
            for item in json.loads(inc.top_features_json):
                top_features.append(FeatureAttribution(**item))

        raw_evidence = []
        if inc.raw_evidence_json:
            raw_evidence = json.loads(inc.raw_evidence_json)

        # Retrieve recommended runbooks based on incident title and top features
        query_text = f"{inc.title} " + " ".join(f.feature for f in top_features[:3])
        runbook_hits = []
        try:
            hits = retrieval_service.search(query_text, top_k=3)
            for h in hits:
                runbook_hits.append({
                    "slug": h.slug,
                    "title": h.title,
                    "score": round(h.score, 4),
                    "excerpt": h.excerpt,
                })
        except Exception:
            pass

        return IncidentDetail(
            incident_id=inc.incident_id,
            block_id=inc.block_id,
            title=inc.title,
            severity=inc.severity,
            status=inc.status,
            anomaly_score=inc.anomaly_score,
            event_count=inc.event_count,
            top_features=top_features,
            raw_evidence=raw_evidence,
            recommended_runbooks=runbook_hits,
            created_at=inc.created_at.isoformat(),
            updated_at=inc.updated_at.isoformat(),
        )

    # ── Dashboard Metrics ──────────────────────────────────────────────────

    async def get_dashboard_metrics(self, db: AsyncSession) -> DashboardMetrics:
        """Compute aggregate system metrics for dashboard."""
        total_logs = (await db.execute(select(func.count(LogEntry.id)))).scalar_one()
        total_incidents = (await db.execute(select(func.count(Incident.id)))).scalar_one()
        open_incidents = (await db.execute(
            select(func.count(Incident.id)).where(Incident.status == IncidentStatus.OPEN)
        )).scalar_one()

        # Count distinct blocks
        distinct_blocks = (await db.execute(
            select(func.count(func.distinct(LogEntry.block_id))).where(LogEntry.block_id.isnot(None))
        )).scalar_one()

        anomaly_rate = (total_incidents / max(distinct_blocks, 1)) * 100.0

        # Severity breakdown
        sev_counts = {}
        for s in IncidentSeverity:
            c = (await db.execute(select(func.count(Incident.id)).where(Incident.severity == s.value))).scalar_one()
            sev_counts[s.value] = c

        # Status breakdown
        stat_counts = {}
        for st in IncidentStatus:
            c = (await db.execute(select(func.count(Incident.id)).where(Incident.status == st.value))).scalar_one()
            stat_counts[st.value] = c

        # Recent 5 incidents
        recent_q = select(Incident).order_by(Incident.created_at.desc()).limit(5)
        recent_rows = (await db.execute(recent_q)).scalars().all()
        recent_summaries = [
            IncidentSummary(
                incident_id=r.incident_id,
                block_id=r.block_id,
                title=r.title,
                severity=r.severity,
                status=r.status,
                anomaly_score=r.anomaly_score,
                event_count=r.event_count,
                created_at=r.created_at.isoformat(),
            )
            for r in recent_rows
        ]

        return DashboardMetrics(
            total_logs_ingested=total_logs,
            total_blocks_analyzed=distinct_blocks,
            total_incidents=total_incidents,
            open_incidents=open_incidents,
            anomaly_rate_percent=round(anomaly_rate, 2),
            severity_breakdown=sev_counts,
            status_breakdown=stat_counts,
            recent_incidents=recent_summaries,
        )


    # ── Similar Incident Retrieval ─────────────────────────────────────────

    _build_incident_context = staticmethod(build_incident_context)

    @staticmethod
    def _sample_representative_evidence(lines: List[str], max_sample: int = 25) -> List[str]:
        """
        Select a bounded, representative sample of evidence lines preserving distinctive early,
        middle, and later lines without unbounded SQL query growth.
        """
        if len(lines) <= max_sample:
            return list(dict.fromkeys(lines))

        selected_indices = list(range(min(10, len(lines))))
        selected_indices.extend(range(max(0, len(lines) - 10), len(lines)))
        middle_pool = range(10, max(10, len(lines) - 10))
        if middle_pool:
            step = max(1, len(middle_pool) // 5)
            selected_indices.extend(list(middle_pool)[::step][:5])

        seen = set()
        sample: List[str] = []
        for idx in sorted(set(selected_indices)):
            line = lines[idx]
            if line not in seen:
                seen.add(line)
                sample.append(line)
                if len(sample) >= max_sample:
                    break
        return sample

    @staticmethod
    def _datetime_diff_seconds(dt1: Optional[datetime], dt2: Optional[datetime]) -> Optional[float]:
        """Safely compute absolute difference in seconds between two datetimes (naive or aware)."""
        if dt1 is None or dt2 is None:
            return None
        from datetime import timezone
        d1 = dt1.astimezone(timezone.utc).replace(tzinfo=None) if dt1.tzinfo is not None else dt1
        d2 = dt2.astimezone(timezone.utc).replace(tzinfo=None) if dt2.tzinfo is not None else dt2
        return abs((d1 - d2).total_seconds())

    @staticmethod
    def _incident_evidence_signature(inc: Incident) -> Optional[Tuple[str, ...]]:
        """
        Extract canonical evidence signature from raw evidence lines.
        Returns None if raw evidence is missing, malformed, or empty.
        Preserves evidence sequence order and normalizes whitespace per line.
        Never falls back to metadata (block_id, title, features).
        """
        raw_json = getattr(inc, "raw_evidence_json", None)
        if not raw_json:
            return None
        try:
            evs = json.loads(raw_json)
            if not isinstance(evs, list) or not evs:
                return None
            normalized = tuple(str(line).strip() for line in evs if str(line).strip())
            return normalized if normalized else None
        except (json.JSONDecodeError, TypeError, ValueError):
            return None

    @staticmethod
    async def _resolve_incident_session_id(inc: Incident, db: Optional[AsyncSession]) -> Optional[str]:
        """
        Resolve session identity for an incident using evidence and LogEntry provenance.

        Strongest available combination:
        a. Exact raw evidence matches across LogEntry records.
        b. Matching block_id where applicable.
        c. LogEntry.created_at proximity to Incident.created_at.
        d. Consistency across multiple matching evidence lines.

        If provenance cannot be established confidently, returns None rather than guessing.
        Transient in-memory session_id is used only as fallback when database provenance
        is absent (e.g. active uncommitted transaction or in-memory unit tests).
        """
        if not inc or not getattr(inc, "raw_evidence_json", None) or db is None:
            sess = getattr(inc, "session_id", None)
            return str(sess) if sess else None

        # 1. Parse raw evidence lines
        try:
            evs = json.loads(inc.raw_evidence_json)
            if not isinstance(evs, list) or not evs:
                sess = getattr(inc, "session_id", None)
                return str(sess) if sess else None
            clean_lines = [str(l).strip() for l in evs if str(l).strip()]
            if not clean_lines:
                sess = getattr(inc, "session_id", None)
                return str(sess) if sess else None
        except (json.JSONDecodeError, TypeError, ValueError):
            sess = getattr(inc, "session_id", None)
            return str(sess) if sess else None

        # 2. Query LogEntry records matching evidence lines
        # Use a bounded representative sample preserving early, middle, and distinctive later lines
        sample_lines = PipelineService._sample_representative_evidence(clean_lines, max_sample=25)
        try:
            q = select(
                LogEntry.session_id,
                LogEntry.created_at,
                LogEntry.raw_line,
                LogEntry.block_id,
            ).where(LogEntry.raw_line.in_(sample_lines))
            rows = (await db.execute(q)).all()
        except SQLAlchemyError as exc:
            logger.warning("Database error during incident session resolution", error=str(exc))
            sess = getattr(inc, "session_id", None)
            return str(sess) if sess else None

        if not rows:
            sess = getattr(inc, "session_id", None)
            return str(sess) if sess else None

        # 3. Analyze candidate sessions
        session_matches: Dict[str, List[tuple]] = {}
        for s_id, le_time, raw_l, b_id in rows:
            if not s_id:
                continue
            session_matches.setdefault(s_id, []).append((le_time, raw_l, b_id))

        if not session_matches:
            sess = getattr(inc, "session_id", None)
            return str(sess) if sess else None

        # Score candidate sessions based on evidence strength
        scored_candidates = []
        target_block = inc.block_id if inc.block_id else None
        target_time = inc.created_at if getattr(inc, "created_at", None) else None

        for s_id, entries in session_matches.items():
            matched_lines = set(str(e[1]).strip() for e in entries)
            line_count = len(matched_lines & set(sample_lines))
            has_block_match = bool(target_block and any(e[2] == target_block for e in entries))

            time_diffs = []
            if target_time:
                for e in entries:
                    if e[0]:
                        t_diff = PipelineService._datetime_diff_seconds(target_time, e[0])
                        if t_diff is not None:
                            time_diffs.append(t_diff)
            min_diff = min(time_diffs) if time_diffs else None

            scored_candidates.append({
                "session_id": s_id,
                "line_count": line_count,
                "line_coverage": line_count / len(sample_lines),
                "has_block_match": has_block_match,
                "min_time_diff": min_diff,
            })

        # If block_id is available and some sessions match the block_id, filter out non-matching blocks
        if target_block and any(c["has_block_match"] for c in scored_candidates):
            scored_candidates = [c for c in scored_candidates if c["has_block_match"]]

        # Sort candidate sessions:
        # 1. line_count descending (most evidence lines matched)
        # 2. min_time_diff ascending (closest in time, treating None as infinity)
        scored_candidates.sort(
            key=lambda c: (
                -c["line_count"],
                c["min_time_diff"] if c["min_time_diff"] is not None else float("inf"),
            )
        )

        top_cand = scored_candidates[0]

        # Check for ambiguity:
        # If top candidate matches the same line count as second candidate:
        if len(scored_candidates) > 1:
            second_cand = scored_candidates[1]
            if top_cand["line_count"] == second_cand["line_count"]:
                top_t = top_cand["min_time_diff"]
                sec_t = second_cand["min_time_diff"]
                # If neither has timestamps or their proximity is indistinguishable (< 5s), it is ambiguous
                if top_t is None or sec_t is None or abs(top_t - sec_t) < 5.0:
                    return None

        # Check confidence for single-line evidence matches:
        # A single matching line alone is not sufficient provenance proof without block and timestamp corroboration.
        if top_cand["line_count"] == 1:
            if not top_cand["has_block_match"]:
                return None
            if top_cand["min_time_diff"] is None or top_cand["min_time_diff"] > 60.0:
                return None
            if len(sample_lines) > 1 and top_cand["min_time_diff"] > 10.0:
                return None

        # If time difference is over 1 day and not all evidence lines matched, do not guess
        if top_cand["min_time_diff"] is not None and top_cand["min_time_diff"] > 86400.0:
            if top_cand["line_coverage"] < 1.0:
                return None

        return top_cand["session_id"]

    @staticmethod
    def _are_duplicate_ingestions(
        inc1: Incident,
        sess1: Optional[str],
        inc2: Incident,
        sess2: Optional[str],
        max_window_seconds: float = 120.0,
    ) -> bool:
        """
        Determine whether two incidents represent duplicate ingestions rather than
        genuinely independent incidents.

        Decision Rules:
        1. Actual Evidence Required:
           If raw evidence is missing, malformed, or empty for either incident,
           they are never classified as duplicates based on metadata.
           Evidence signatures must match identically.

        2. Provenance & Timing Rules:
           a) Same non-empty session identity:
              If sess1 and sess2 and sess1 == sess2 -> duplicate ingestion (True).
           b) Distinct non-empty session identities:
              If sess1 and sess2 and sess1 != sess2:
                 - If time_diff is None (missing timestamp on either):
                   Never deduplicate solely because block IDs match (False).
                 - If time_diff <= max_window_seconds and inc1.block_id == inc2.block_id:
                   Duplicate burst within ingestion window on same block (True).
                 - If time_diff > max_window_seconds:
                   Independent historical incidents (False).
           c) Missing/indeterminate session identity on either incident:
              - If time_diff is None:
                Missing session identity + missing timestamp -> never duplicate (False).
              - If time_diff <= max_window_seconds and inc1.block_id == inc2.block_id:
                Duplicate burst within ingestion window on same block (True).
              - If time_diff > max_window_seconds:
                Independent historical incidents (False).
        """
        sig1 = PipelineService._incident_evidence_signature(inc1)
        sig2 = PipelineService._incident_evidence_signature(inc2)
        if sig1 is None or sig2 is None or sig1 != sig2:
            return False

        t1 = getattr(inc1, "created_at", None)
        t2 = getattr(inc2, "created_at", None)
        time_diff: Optional[float] = PipelineService._datetime_diff_seconds(t1, t2)

        # Case A: Same non-empty session identity establishes duplicate provenance
        if sess1 and sess2 and sess1 == sess2:
            return True

        # Case B: Distinct non-empty session identities
        if sess1 and sess2 and sess1 != sess2:
            # If timestamps missing, must not deduplicate solely because block IDs match
            if time_diff is None:
                return False
            # Check 120-second boundary: time_diff <= max_window_seconds
            if time_diff <= max_window_seconds:
                return bool(inc1.block_id and inc2.block_id and inc1.block_id == inc2.block_id)
            return False

        # Case C: One or both session identities are missing / None / empty
        # Missing session identity and missing timestamps must never establish a duplicate burst
        if time_diff is None:
            return False

        if time_diff <= max_window_seconds:
            return bool(inc1.block_id and inc2.block_id and inc1.block_id == inc2.block_id)

        return False

    async def get_similar_incidents(
        self,
        incident_id: str,
        db: AsyncSession,
        top_k: int = 5,
    ) -> Optional[dict]:
        """
        Find incidents whose descriptions/contexts are most similar to the given incident.

        Similarity is computed by embedding the comprehensive incident context
        (description, title, features, and log evidence) with the retrieval
        service's embedding model (cosine similarity). When sentence-transformers
        is unavailable, TF-IDF / token lexical similarity is used instead;
        the ``search_mode`` field indicates which method was applied.

        Returns None when the incident_id is not found.
        """
        # Fetch the target incident
        q = select(Incident).where(Incident.incident_id == incident_id)
        res = await db.execute(q)
        target = res.scalars().first()
        if not target:
            return None

        query_text = self._build_incident_context(target)

        # Fetch all other incidents
        all_q = select(Incident).where(Incident.incident_id != incident_id)
        all_res = await db.execute(all_q)
        candidates = all_res.scalars().all()

        if not candidates:
            return {
                "incident_id": incident_id,
                "query_text": query_text,
                "search_mode": "none",
                "similar_incidents": [],
            }

        # Build candidate comparison texts
        cand_texts = [self._build_incident_context(c) for c in candidates]

        # Try semantic similarity first
        target_emb = retrieval_service.embed_text(query_text)
        search_mode = "semantic" if target_emb is not None else "lexical"

        scored: list = []

        if target_emb is not None:
            try:
                # Semantic: embed all candidate contexts and compute cosine similarity
                import faiss  # noqa: PLC0415
                cand_embs = retrieval_service._embed(cand_texts)
                faiss.normalize_L2(cand_embs)
                # target_emb is already normalised by embed_text()
                sims = cand_embs @ target_emb  # shape: (n_candidates,)
                for inc, sim in zip(candidates, sims):
                    scored.append((inc, float(sim)))
            except Exception as exc:
                logger.warning("Semantic embedding for candidate texts failed, falling back to lexical", error=str(exc))
                target_emb = None
                search_mode = "lexical"

        if target_emb is None:
            # Lexical fallback: TF-IDF cosine similarity on comparison texts
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: PLC0415
                from sklearn.metrics.pairwise import cosine_similarity  # noqa: PLC0415
                vectorizer = TfidfVectorizer(stop_words="english")
                tfidf = vectorizer.fit_transform(cand_texts + [query_text])
                sims = cosine_similarity(tfidf[-1], tfidf[:-1])[0]
                for inc, sim in zip(candidates, sims):
                    scored.append((inc, float(sim)))
            except ImportError:
                # Token-based lexical fallback when sklearn is unavailable
                q_words = set(re.findall(r"[a-z0-9_-]+", query_text.lower()))
                for inc, c_text in zip(candidates, cand_texts):
                    cand_words = set(re.findall(r"[a-z0-9_-]+", c_text.lower()))
                    overlap = len(q_words & cand_words) / max(len(q_words), 1) if q_words else 0.0
                    scored.append((inc, float(overlap)))

        # Helper to determine if an incident represents an active error/outage failure
        def _is_error_incident(inc: Incident) -> bool:
            if inc.severity and inc.severity.value in ("CRITICAL", "HIGH"):
                return True
            if inc.top_features_json:
                try:
                    feats = json.loads(inc.top_features_json)
                    if any(
                        f.get("feature") in ("error_count", "has_error") and float(f.get("value", 0)) > 0
                        for f in feats
                        if isinstance(f, dict)
                    ):
                        return True
                except (ValueError, TypeError):
                    pass
            if inc.raw_evidence_json:
                try:
                    evs = json.loads(inc.raw_evidence_json)
                    if isinstance(evs, list) and any(
                        any(w in str(line).lower() for w in ("error", "exception", "fail", "timeout", "critical", "fatal", "panic"))
                        for line in evs
                    ):
                        return True
                except (ValueError, TypeError):
                    pass
            return False

        target_is_error = _is_error_incident(target)
        target_sess = await self._resolve_incident_session_id(target, db)

        # Sort candidate results by similarity descending
        scored.sort(key=lambda x: x[1], reverse=True)

        # Filter by defensible similarity threshold, operational event compatibility,
        # and duplicate incident suppression (prevent duplicate ingestions from appearing as independent matches,
        # while preserving genuinely independent historical incidents with identical evidence).
        # Provisional semantic similarity threshold: 0.50 (for compatible event types), lexical: 0.20
        min_sim = 0.50 if search_mode == "semantic" else 0.20
        filtered_scored = []
        accepted_provenance: list = []  # list of (inc, session_id)

        for inc, sim in scored:
            if sim < min_sim:
                continue
            cand_is_error = _is_error_incident(inc)
            # Operational compatibility check: routine status notifications must never match active outage failures
            if target_is_error != cand_is_error:
                continue

            cand_sess = await self._resolve_incident_session_id(inc, db)

            # Deduplication Check 1: Exclude duplicate ingestion records of the target incident itself.
            # When an identical log batch is ingested multiple times within the same session or ingestion burst,
            # duplicate records share the same evidence and provenance. Independent sessions are NOT discarded.
            if self._are_duplicate_ingestions(target, target_sess, inc, cand_sess):
                continue

            # Deduplication Check 2: Exclude duplicate records among historical candidates.
            # If an identical-evidence candidate was already accepted from the same provenance or ingestion window,
            # consolidate it. If candidates originate from distinct sessions and independent ingestion windows,
            # both remain eligible as separate historical matches.
            is_dup_candidate = False
            for accepted_inc, accepted_sess in accepted_provenance:
                if self._are_duplicate_ingestions(accepted_inc, accepted_sess, inc, cand_sess):
                    is_dup_candidate = True
                    break
            if is_dup_candidate:
                continue

            filtered_scored.append((inc, sim))
            accepted_provenance.append((inc, cand_sess))

        top = filtered_scored[:top_k]

        from backend.api.schemas import SimilarIncidentResult, SimilarIncidentsResponse  # noqa: PLC0415
        results = [
            SimilarIncidentResult(
                incident_id=inc.incident_id,
                block_id=inc.block_id,
                title=inc.title,
                severity=inc.severity,
                status=inc.status,
                anomaly_score=inc.anomaly_score,
                similarity_score=round(sim, 4),
                search_mode=search_mode,
                created_at=inc.created_at.isoformat(),
            )
            for inc, sim in top
        ]

        return {
            "incident_id": incident_id,
            "query_text": query_text,
            "search_mode": search_mode,
            "similar_incidents": results,
        }

    # ── Incident Runbook Retrieval ─────────────────────────────────────────

    async def get_incident_runbooks(
        self,
        incident_id: str,
        db: AsyncSession,
        top_k: int = 3,
        min_score: Optional[float] = None,
    ) -> Optional[dict]:
        """
        Retrieve the top-k most relevant runbooks for a given incident.

        Constructs an evidence-grounded search query using clean log lines,
        descriptive incident title, and active anomaly features.
        Enforces a defensible relevance threshold (0.50 for semantic, 0.25 for lexical).
        Returns None when the incident_id is not found.
        """
        q = select(Incident).where(Incident.incident_id == incident_id)
        res = await db.execute(q)
        inc = res.scalars().first()
        if not inc:
            return None

        # 1. Parse raw log evidence
        evidence_lines: List[str] = []
        if inc.raw_evidence_json:
            try:
                ev_data = json.loads(inc.raw_evidence_json)
                if isinstance(ev_data, list):
                    evidence_lines = [str(x).strip() for x in ev_data if str(x).strip()]
            except (ValueError, TypeError):
                evidence_lines = []

        # Clean evidence lines (strip timestamps and log levels)
        import re
        clean_lines: List[str] = []
        for line in evidence_lines[:5]:
            s = re.sub(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?\s*", "", line)
            s = re.sub(r"^(?:INFO|WARN|WARNING|ERROR|CRITICAL|DEBUG)\s+", "", s, flags=re.IGNORECASE)
            s = s.strip()
            if s and s not in clean_lines:
                clean_lines.append(s)

        # 2. Extract active features (value > 0)
        top_features = []
        if inc.top_features_json:
            try:
                top_features = json.loads(inc.top_features_json)
            except (ValueError, TypeError):
                top_features = []

        active_terms = [
            f.get("feature", "")
            for f in top_features
            if isinstance(f, dict) and float(f.get("value", 0)) > 0 and f.get("feature") not in ("event_count",)
        ]

        # 3. Formulate query: prioritize actual log evidence over generic template titles
        query_parts: List[str] = []
        if inc.title and not re.match(r"^Anomalous\s+Block\s+Activity\s+on\s+", inc.title, flags=re.IGNORECASE):
            query_parts.append(inc.title.strip())

        if clean_lines:
            query_parts.append(" ".join(clean_lines[:3]))
        elif not query_parts:
            query_parts.append(inc.title.strip() if inc.title else getattr(inc, "block_id", ""))

        if active_terms:
            query_parts.append(" ".join(active_terms[:2]))

        query_text = " ".join(query_parts).strip() or inc.title or getattr(inc, "block_id", "")

        try:
            details = retrieval_service.search_detail(query_text, top_k=top_k)
        except Exception as exc:
            logger.warning("Runbook search failed", error=str(exc))
            details = []

        search_mode = details[0].search_mode if details else "unavailable"

        # Apply defensible relevance threshold:
        # Never force irrelevant runbooks into reports.
        # Keep lexical retrieval high enough to reject generic token overlap.
        threshold = min_score if min_score is not None else (0.50 if search_mode == "semantic" else 0.25)
        filtered_details = [d for d in details if d.score >= threshold]

        from backend.api.schemas import RunbookDetailOut, IncidentRunbooksResponse  # noqa: PLC0415
        runbook_outs = [
            RunbookDetailOut(
                slug=d.slug,
                id=d.id,
                title=d.title,
                score=round(d.score, 4),
                search_mode=d.search_mode,
                tags=d.tags,
                symptoms=d.symptoms,
                possible_causes=d.possible_causes,
                investigation_steps=d.investigation_steps,
                remediation=d.remediation,
                verification_steps=d.verification_steps,
                escalation=d.escalation,
            )
            for d in filtered_details
        ]

        return {
            "incident_id": incident_id,
            "query_text": query_text,
            "search_mode": search_mode,
            "runbooks": runbook_outs,
        }


pipeline_service = PipelineService()
