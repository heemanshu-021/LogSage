"""
LogSage Isolation Forest Anomaly Detection Engine.

Architecture & Mechanics:
- Isolation Forest isolates anomalies by randomly partitioning feature dimensions with recursive axis-aligned splits.
- Anomalous instances (e.g., blocks with unusual error bursts, rare event cascades, or abnormal trace lengths)
  require significantly fewer splits to isolate, resulting in shorter average path lengths in the ensemble trees.
- Contamination Selection:
  In HDFS, exploration established that anomalous blocks represent ~2.9% to 3.9% of all blocks.
  Setting `contamination=0.04` aligns the baseline split threshold with the empirical prior without overfitting.
- Threshold Tuning:
  Provides both sklearn offset-based classification and continuous [0, 1] anomaly scoring,
  allowing operators to adjust thresholds according to triage sensitivity.
"""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import IsolationForest

from backend.core.logging import get_logger
from ml.preprocessing.feature_extraction import BlockFeatureExtractor

logger = get_logger(__name__)


class IsolationForestDetector:
    """Production Isolation Forest model for LogSage log anomaly triage."""

    def __init__(
        self,
        n_estimators: int = 150,
        max_samples: Union[str, int, float] = "auto",
        contamination: float = 0.04,
        random_state: int = 42,
        threshold: float = 0.5,
    ):
        """
        Args:
            n_estimators: Number of isolation trees in ensemble.
            max_samples: Number of samples drawn from X to train each tree.
            contamination: Expected anomaly fraction prior (0.04 for HDFS baseline).
            random_state: Seed for reproducible splits.
            threshold: Decision boundary on normalised score [0, 1].
        """
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.contamination = contamination
        self.random_state = random_state
        self.threshold = threshold

        self.model = IsolationForest(
            n_estimators=self.n_estimators,
            max_samples=self.max_samples,
            contamination=self.contamination,
            random_state=self.random_state,
            n_jobs=-1,
        )
        self.is_fitted: bool = False
        self.score_min_: float = 0.0
        self.score_max_: float = 1.0

    def fit(self, X: np.ndarray) -> "IsolationForestDetector":
        """
        Fit Isolation Forest ensemble on numerical training matrix.
        X shape: (n_samples, n_features)
        """
        if len(X) == 0:
            raise ValueError("Training matrix X cannot be empty.")

        logger.info(
            "Fitting IsolationForest",
            n_samples=X.shape[0],
            n_features=X.shape[1],
            contamination=self.contamination,
        )
        self.model.fit(X)
        self.is_fitted = True

        # Calibrate score bounds for normalization
        raw_scores = -self.model.decision_function(X)
        self.score_min_ = float(raw_scores.min())
        self.score_max_ = float(raw_scores.max()) if raw_scores.max() > raw_scores.min() else (self.score_min_ + 1.0)

        logger.info("IsolationForest fitted successfully", score_min=self.score_min_, score_max=self.score_max_)
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        """
        Compute continuous anomaly scores in [0, 1].
        Higher score = more anomalous.
        """
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted. Call fit() before scoring.")

        # sklearn decision_function is negative for outliers, positive for inliers
        raw_scores = -self.model.decision_function(X)
        span = self.score_max_ - self.score_min_
        if span <= 1e-9:
            return np.zeros(len(X), dtype=np.float32)

        normalised = (raw_scores - self.score_min_) / span
        return np.clip(normalised, 0.0, 1.0).astype(np.float32)

    def predict(self, X: np.ndarray, threshold: Optional[float] = None) -> np.ndarray:
        """
        Predict binary labels (1 = Anomaly, 0 = Normal).
        
        Args:
            X: Feature matrix.
            threshold: Optional custom cutoff on normalised score [0, 1].
                       If None, uses sklearn's contamination offset.
        """
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted. Call fit() before predicting.")

        if threshold is not None:
            scores = self.score(X)
            return (scores >= threshold).astype(int)

        # Use native sklearn prediction: -1 = outlier, 1 = inlier
        raw_preds = self.model.predict(X)
        return (raw_preds == -1).astype(int)

    # ── Inference Utilities ────────────────────────────────────────────────

    def predict_block(
        self,
        block_id: str,
        events: List[Dict[str, Any]],
        extractor: BlockFeatureExtractor,
        threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        End-to-end inference for a single block's event stream.
        
        Returns:
            Dictionary with block_id, anomaly_score, is_anomaly, and top features.
        """
        block_dict = {block_id: events}
        X, _ = extractor.transform(block_dict)

        if len(X) == 0:
            return {
                "block_id": block_id,
                "anomaly_score": 0.0,
                "is_anomaly": False,
                "label": "Normal",
                "top_features": [],
            }

        score = float(self.score(X)[0])
        pred = int(self.predict(X, threshold=threshold)[0])

        # Extract top feature values
        feature_vector = X[0]
        top_features = []
        if extractor.feature_names_:
            sorted_indices = np.argsort(np.abs(feature_vector))[::-1][:5]
            for idx in sorted_indices:
                top_features.append({
                    "feature": extractor.feature_names_[idx],
                    "value": float(feature_vector[idx]),
                })

        return {
            "block_id": block_id,
            "anomaly_score": round(score, 4),
            "is_anomaly": bool(pred == 1),
            "label": "Anomaly" if pred == 1 else "Normal",
            "top_features": top_features,
        }

    # ── Model Persistence ──────────────────────────────────────────────────

    def save(self, filepath: str | Path) -> None:
        """Save model and calibration state using joblib."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "model": self.model,
            "n_estimators": self.n_estimators,
            "max_samples": self.max_samples,
            "contamination": self.contamination,
            "random_state": self.random_state,
            "threshold": self.threshold,
            "is_fitted": self.is_fitted,
            "score_min_": self.score_min_,
            "score_max_": self.score_max_,
            "sklearn_version": sklearn.__version__,
        }
        joblib.dump(payload, filepath)
        logger.info("Saved IsolationForestDetector", path=str(filepath))

    @classmethod
    def load(cls, filepath: str | Path) -> "IsolationForestDetector":
        """Load trained model and calibration state from disk."""
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Model file not found: {filepath}")

        payload = joblib.load(filepath)
        saved_sklearn_version = payload.get("sklearn_version")
        if saved_sklearn_version and saved_sklearn_version != sklearn.__version__:
            raise RuntimeError(
                "Isolation Forest artifact was saved with scikit-learn "
                f"{saved_sklearn_version}, but runtime has {sklearn.__version__}. "
                "Retrain or load the artifact with its matching scikit-learn version."
            )
        detector = cls(
            n_estimators=payload["n_estimators"],
            max_samples=payload["max_samples"],
            contamination=payload["contamination"],
            random_state=payload["random_state"],
            threshold=payload["threshold"],
        )
        detector.model = payload["model"]
        detector.is_fitted = payload["is_fitted"]
        detector.score_min_ = payload["score_min_"]
        detector.score_max_ = payload["score_max_"]
        logger.info("Loaded IsolationForestDetector", path=str(filepath))
        return detector
