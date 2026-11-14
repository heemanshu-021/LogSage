"""
Ingest service — orchestrates: parse → featurise → detect → persist.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.logging import get_logger
from backend.db.models import Anomaly, AnomalyLabel, LogEntry, LogSource
from ml.parser.drain_parser import DrainParser, ParseResult
from ml.preprocessing.feature_extractor import FeatureExtractor
from ml.models.isolation_forest import IsolationForestDetector

logger = get_logger(__name__)

# Module-level singletons (re-used across requests)
_parser = DrainParser()
_extractor = FeatureExtractor()
_detector = IsolationForestDetector(threshold=0.5, contamination=0.1)
_detector_fitted = False


def get_parser() -> DrainParser:
    return _parser


async def ingest_and_detect(
    lines: List[str],
    source: str,
    session_id: Optional[str],
    db: AsyncSession,
) -> Tuple[int, int]:
    """
    Full pipeline:
      1. Parse each line with Drain3
      2. Persist LogEntry rows
      3. Featurise + anomaly-detect (if enough data)
      4. Persist Anomaly rows for flagged entries

    Returns (n_ingested, n_anomalies).
    """
    global _detector_fitted

    if not lines:
        return 0, 0

    # 1. Parse
    parse_results: List[ParseResult] = []
    db_entries: List[LogEntry] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        pr = _parser.parse(line)
        parse_results.append(pr)
        entry = LogEntry(
            raw_line=pr.raw_line,
            template=pr.template,
            template_id=pr.template_id,
            source=LogSource(source) if source in LogSource._value2member_map_ else LogSource.API,
            session_id=session_id,
        )
        db_entries.append(entry)

    if not db_entries:
        return 0, 0

    # 2. Persist log entries
    session_added = db_entries
    db.add_all(session_added)
    await db.flush()   # get IDs without committing

    # 3. Featurise + detect
    n_anomalies = 0
    min_samples = 10

    if len(parse_results) >= min_samples:
        try:
            if not _detector_fitted:
                X = _extractor.fit_transform(parse_results)
                _detector.fit(X)
                _detector_fitted = True
            else:
                X = _extractor.transform(parse_results)

            scores = _detector.score(X)
            labels = _detector.predict(X)

            for entry, score, label in zip(session_added, scores, labels):
                if label == 1:
                    anomaly = Anomaly(
                        log_entry_id=entry.id,
                        score=float(score),
                        label=AnomalyLabel.ANOMALY,
                        detector="isolation_forest",
                    )
                    db.add(anomaly)
                    n_anomalies += 1
        except Exception as exc:
            logger.warning("Anomaly detection failed", error=str(exc))

    await db.commit()
    logger.info(
        "Ingest complete",
        n_lines=len(db_entries),
        n_anomalies=n_anomalies,
    )
    return len(db_entries), n_anomalies
