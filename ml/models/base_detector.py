"""Abstract base class for all anomaly detectors."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

import numpy as np


class BaseDetector(ABC):
    """
    All LogSage anomaly detectors must implement this interface.

    fit(X)         → train on feature matrix X (shape: [n_samples, n_features])
    predict(X)     → return binary labels array (1=anomaly, 0=normal)
    score(X)       → return raw anomaly scores (higher = more anomalous)
    save(path)     → persist model to disk
    load(path)     → class method to reload from disk
    """

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self._fitted = False

    @abstractmethod
    def fit(self, X: np.ndarray) -> "BaseDetector":
        ...

    @abstractmethod
    def score(self, X: np.ndarray) -> np.ndarray:
        """Return anomaly score per sample. Higher = more anomalous."""
        ...

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Return binary labels (1=anomaly, 0=normal) using threshold."""
        scores = self.score(X)
        return (scores >= self.threshold).astype(int)

    @abstractmethod
    def save(self, path: str) -> None:
        ...

    @classmethod
    @abstractmethod
    def load(cls, path: str) -> "BaseDetector":
        ...

    def _require_fitted(self) -> None:
        if not self._fitted:
            raise RuntimeError(f"{self.__class__.__name__} is not fitted. Call fit() first.")
