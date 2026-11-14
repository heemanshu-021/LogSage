"""Unit tests for anomaly detectors."""
from __future__ import annotations

import numpy as np
import pytest

from ml.models.isolation_forest import IsolationForestDetector
from ml.models.lof import LOFDetector
from ml.evaluation.metrics import evaluate, DetectionMetrics


def _make_data(n_normal: int = 100, n_anomaly: int = 10, seed: int = 42):
    rng = np.random.default_rng(seed)
    X_normal  = rng.standard_normal((n_normal, 10))
    X_anomaly = rng.standard_normal((n_anomaly, 10)) * 5 + 10   # far from normal
    X = np.vstack([X_normal, X_anomaly])
    y = np.array([0] * n_normal + [1] * n_anomaly)
    return X, y


class TestIsolationForest:
    def test_fit_predict_shape(self):
        X, _ = _make_data()
        det = IsolationForestDetector(contamination=0.1)
        det.fit(X)
        preds = det.predict(X)
        assert preds.shape == (len(X),)
        assert set(preds).issubset({0, 1})

    def test_scores_in_range(self):
        X, _ = _make_data()
        det = IsolationForestDetector(contamination=0.1)
        det.fit(X)
        scores = det.score(X)
        assert scores.min() >= 0.0
        assert scores.max() <= 1.0

    def test_detects_outliers(self):
        X, y = _make_data(n_normal=200, n_anomaly=20)
        det = IsolationForestDetector(contamination=0.09, threshold=0.5)
        det.fit(X)
        preds = det.predict(X)
        metrics = evaluate(y, preds)
        # Should achieve at least 50% recall on obvious outliers
        assert metrics.recall >= 0.5, f"Recall too low: {metrics.recall}"

    def test_predict_before_fit_raises(self):
        det = IsolationForestDetector()
        with pytest.raises(RuntimeError, match="not fitted"):
            det.predict(np.zeros((5, 10)))

    def test_save_load(self, tmp_path):
        X, _ = _make_data()
        det = IsolationForestDetector()
        det.fit(X)
        path = str(tmp_path / "if_model.pkl")
        det.save(path)
        loaded = IsolationForestDetector.load(path)
        # Scores should be identical after reload
        np.testing.assert_array_almost_equal(det.score(X), loaded.score(X))


class TestLOFDetector:
    def test_fit_predict_shape(self):
        X, _ = _make_data(n_normal=50, n_anomaly=5)
        det = LOFDetector(n_neighbors=5, contamination=0.1)
        det.fit(X)
        preds = det.predict(X)
        assert preds.shape == (len(X),)

    def test_scores_in_range(self):
        X, _ = _make_data(n_normal=50, n_anomaly=5)
        det = LOFDetector(n_neighbors=5, contamination=0.1)
        det.fit(X)
        scores = det.score(X)
        assert scores.min() >= 0.0
        assert scores.max() <= 1.0


class TestMetrics:
    def test_perfect_predictions(self):
        y = np.array([0, 0, 1, 1])
        preds = np.array([0, 0, 1, 1])
        m = evaluate(y, preds)
        assert m.precision == 1.0
        assert m.recall == 1.0
        assert m.f1 == 1.0

    def test_all_wrong(self):
        y = np.array([0, 0, 1, 1])
        preds = np.array([1, 1, 0, 0])
        m = evaluate(y, preds)
        assert m.f1 == 0.0

    def test_metrics_str(self):
        y = np.array([0, 1, 1])
        preds = np.array([0, 1, 0])
        m = evaluate(y, preds)
        s = str(m)
        assert "Precision" in s
        assert "Recall" in s

    def test_auc_with_scores(self):
        y = np.array([0, 0, 0, 1, 1])
        preds = np.array([0, 0, 0, 1, 1])
        scores = np.array([0.1, 0.2, 0.3, 0.8, 0.9])
        m = evaluate(y, preds, scores=scores)
        assert m.auc_roc is not None
        assert 0.0 <= m.auc_roc <= 1.0
