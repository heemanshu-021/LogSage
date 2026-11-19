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
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import (
    AnalyzeResponse,
    DashboardMetrics,
    FeatureAttribution,
    IncidentDetail,
    IncidentSummary,
)
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
        self.extractor: Optional[BlockFeatureExtractor] = None
        self.detector: Optional[IsolationForestDetector] = None
        self._initialise()

    def _initialise(self) -> None:
        """Load parser config and trained ML artifacts."""
        try:
            config_ini = Path("ml/parser/parser_config.ini")
            self.parser = DrainParser(config_path=config_ini if config_ini.exists() else None)
        except Exception as e:
            logger.warning("DrainParser initialisation fallback", error=str(e))
            self.parser = DrainParser()

        model_path = Path("ml/models/saved/isolation_forest.joblib")
        extractor_path = Path("ml/models/saved/feature_extractor.json")

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
        return (self.detector is not None and self.detector.is_fitted and
                self.extractor is not None and self.extractor.is_fitted)

    def _determine_severity(self, score: float, has_error: bool) -> IncidentSeverity:
        if score >= 0.85 or has_error:
            return IncidentSeverity.CRITICAL
        elif score >= 0.65:
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
            b_id = pr.block_ids[0] if pr.block_ids else None
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

        # Sort descending by similarity score
        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:top_k]

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
    ) -> Optional[dict]:
        """
        Retrieve the top-k most relevant runbooks for a given incident.

        The incident title and top feature names are combined to form a
        descriptive query that is passed to the retrieval service's
        search_detail() method.

        Returns None when the incident_id is not found.
        """
        q = select(Incident).where(Incident.incident_id == incident_id)
        res = await db.execute(q)
        inc = res.scalars().first()
        if not inc:
            return None

        # Build query from incident title + top feature names
        top_features = []
        if inc.top_features_json:
            try:
                top_features = json.loads(inc.top_features_json)
            except (ValueError, TypeError):
                top_features = []

        feature_terms = " ".join(f.get("feature", "") for f in top_features[:3])
        query_text = f"{inc.title} {feature_terms}".strip()

        try:
            details = retrieval_service.search_detail(query_text, top_k=top_k)
        except Exception as exc:
            logger.warning("Runbook search failed", error=str(exc))
            details = []

        search_mode = details[0].search_mode if details else "unavailable"

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
            for d in details
        ]

        return {
            "incident_id": incident_id,
            "query_text": query_text,
            "search_mode": search_mode,
            "runbooks": runbook_outs,
        }


pipeline_service = PipelineService()
