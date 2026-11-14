"""Isolation Forest anomaly detector."""
from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
from sklearn.ensemble import IsolationForest

from ml.models.base_detector import BaseDetector
from backend.core.logging import get_logger

logger = get_logger(__name__)


class IsolationForestDetector(BaseDetector):
    """
    Wraps sklearn IsolationForest.

    Scores are normalised to [0, 1] where 1 = most anomalous.
    """

    def __init__(
        self,
        threshold: float = 0.5,
        n_estimators: int = 100,
        contamination: float = 0.1,
        random_state: int = 42,
    ):
        super().__init__(threshold=threshold)
        self._model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1,
        )

    def fit(self, X: np.ndarray) -> "IsolationForestDetector":
        logger.info("IsolationForestDetector fitting", n_samples=X.shape[0])
        self._model.fit(X)
        self._fitted = True
        logger.info("IsolationForestDetector fitted ✓")
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        """
        sklearn's decision_function returns negative values for anomalies.
        We invert and normalise so that higher score = more anomalous.
        """
        self._require_fitted()
        raw = self._model.decision_function(X)        # more negative → anomaly
        inverted = -raw                                # more positive → anomaly
        # Normalise to [0, 1]
        lo, hi = inverted.min(), inverted.max()
        if hi - lo < 1e-9:
            return np.zeros(len(X))
        return (inverted - lo) / (hi - lo)

    def save(self, path: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "wb") as f:
            pickle.dump(self._model, f)
        logger.info("IsolationForestDetector saved", path=path)

    @classmethod
    def load(cls, path: str) -> "IsolationForestDetector":
        with open(path, "rb") as f:
            model = pickle.load(f)
        instance = cls()
        instance._model = model
        instance._fitted = True
        logger.info("IsolationForestDetector loaded", path=path)
        return instance
