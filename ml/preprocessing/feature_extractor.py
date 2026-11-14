"""
Feature extraction for anomaly detection.

Converts a list of ParseResult objects (or template strings) into
a numeric feature matrix using TF-IDF on log templates + count-based signals.
"""
from __future__ import annotations

import re
from typing import List, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler

from ml.parser.drain_parser import ParseResult
from backend.core.logging import get_logger

logger = get_logger(__name__)


class FeatureExtractor:
    """
    Encodes log parse results into a numeric matrix.

    Two feature groups:
      1. TF-IDF on the template string   (sparse → dense truncated)
      2. Hand-crafted signals:
           - has_error   (1 if ERROR/CRITICAL in raw line)
           - has_warn    (1 if WARN/WARNING)
           - param_count (number of extracted parameters)
           - line_length (normalised raw line length)
    """

    _ERROR_RE = re.compile(r"\b(ERROR|CRITICAL|FATAL|EXCEPTION)\b", re.IGNORECASE)
    _WARN_RE  = re.compile(r"\b(WARN|WARNING)\b", re.IGNORECASE)

    def __init__(self, max_tfidf_features: int = 100):
        self.max_tfidf_features = max_tfidf_features
        self._vectoriser = TfidfVectorizer(
            max_features=max_tfidf_features,
            token_pattern=r"[A-Za-z_][A-Za-z0-9_]*",
            sublinear_tf=True,
        )
        self._scaler = StandardScaler()
        self._fitted = False

    # ── Fit ────────────────────────────────────────────────────────────────

    def fit(self, results: List[ParseResult]) -> "FeatureExtractor":
        templates = [r.template for r in results]
        self._vectoriser.fit(templates)
        X = self._extract(results)
        self._scaler.fit(X)
        self._fitted = True
        logger.info("FeatureExtractor fitted", n_samples=len(results))
        return self

    # ── Transform ──────────────────────────────────────────────────────────

    def transform(self, results: List[ParseResult]) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("Call fit() before transform().")
        X = self._extract(results)
        return self._scaler.transform(X)

    def fit_transform(self, results: List[ParseResult]) -> np.ndarray:
        self.fit(results)
        return self._scaler.transform(self._extract(results))

    # ── Internal ──────────────────────────────────────────────────────────

    def _extract(self, results: List[ParseResult]) -> np.ndarray:
        templates = [r.template for r in results]
        tfidf = self._vectoriser.transform(templates).toarray()

        hand = np.array([
            [
                1.0 if self._ERROR_RE.search(r.raw_line) else 0.0,
                1.0 if self._WARN_RE.search(r.raw_line) else 0.0,
                float(len(r.parameters)),
                float(len(r.raw_line)),
            ]
            for r in results
        ])
        return np.hstack([tfidf, hand])

    @property
    def feature_dim(self) -> int:
        return self.max_tfidf_features + 4   # TF-IDF + 4 hand-crafted
