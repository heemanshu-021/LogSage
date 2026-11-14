"""Local Outlier Factor anomaly detector."""
from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
from sklearn.neighbors import LocalOutlierFactor

from ml.models.base_detector import BaseDetector
from backend.core.logging import get_logger

logger = get_logger(__name__)


class LOFDetector(BaseDetector):
    """
    Wraps sklearn LocalOutlierFactor in novelty=True mode so it can
    score unseen samples at inference time.
    """

    def __init__(
        self,
        threshold: float = 0.5,
        n_neighbors: int = 20,
        contamination: float = 0.1,
    ):
        super().__init__(threshold=threshold)
        self._model = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=contamination,
            novelty=True,         # required to call predict on new data
            n_jobs=-1,
        )

    def fit(self, X: np.ndarray) -> "LOFDetector":
        logger.info("LOFDetector fitting", n_samples=X.shape[0])
        self._model.fit(X)
        self._fitted = True
        logger.info("LOFDetector fitted ✓")
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        self._require_fitted()
        raw = self._model.decision_function(X)   # negative → outlier
        inverted = -raw
        lo, hi = inverted.min(), inverted.max()
        if hi - lo < 1e-9:
            return np.zeros(len(X))
        return (inverted - lo) / (hi - lo)

    def save(self, path: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "wb") as f:
            pickle.dump(self._model, f)
        logger.info("LOFDetector saved", path=path)

    @classmethod
    def load(cls, path: str) -> "LOFDetector":
        with open(path, "rb") as f:
            model = pickle.load(f)
        instance = cls()
        instance._model = model
        instance._fitted = True
        logger.info("LOFDetector loaded", path=path)
        return instance
