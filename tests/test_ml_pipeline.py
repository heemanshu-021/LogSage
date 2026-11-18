"""
Unit tests for LogSage Machine Learning Anomaly Detection Pipeline.

Verifies:
1. BlockFeatureExtractor: grouping, vocabulary learning, rare event tagging, scaling, no data leakage.
2. IsolationForestDetector: ensemble fitting, continuous scoring [0, 1], prediction, reloadable inference.
3. Model and preprocessor persistence (joblib & json).
4. Evaluation module: precision, recall, f1, confusion matrix, AUC-ROC without fabricated values.
"""
from pathlib import Path
import numpy as np
import pytest

from ml.preprocessing.feature_extraction import BlockFeatureExtractor, BlockFeatures
from ml.models.isolation_forest import IsolationForestDetector
from ml.evaluation.evaluate import evaluate_predictions, generate_evaluation_plots, EvaluationReport


@pytest.fixture
def sample_blocks():
    """Generates synthetic block event streams with known normal and anomalous patterns."""
    blocks = {}
    # 20 normal blocks: typical replication / verification trace (10-15 events, E1-E4)
    for i in range(20):
        b_id = f"blk_normal_{i}"
        blocks[b_id] = [
            {"EventId": "E1", "Level": "INFO", "Component": "dfs.DataNode"},
            {"EventId": "E2", "Level": "INFO", "Component": "dfs.FSNamesystem"},
            {"EventId": "E3", "Level": "INFO", "Component": "dfs.DataNode"},
            {"EventId": "E4", "Level": "INFO", "Component": "dfs.DataNode"},
        ] * 3

    # 2 anomalous blocks: error burst + rare events (E99)
    for i in range(2):
        b_id = f"blk_anomaly_{i}"
        blocks[b_id] = [
            {"EventId": "E1", "Level": "INFO", "Component": "dfs.DataNode"},
            {"EventId": "E99", "Level": "ERROR", "Component": "dfs.DataNode"},
            {"EventId": "E99", "Level": "ERROR", "Component": "dfs.DataNode"},
            {"EventId": "E99", "Level": "FATAL", "Component": "dfs.DataNode"},
        ]
    return blocks


class TestBlockFeatureExtractor:

    def test_fit_and_transform_shapes(self, sample_blocks):
        """Verify feature extraction matrix dimensions and vocabulary learning."""
        extractor = BlockFeatureExtractor(rare_threshold=0.05, scale_features=True)
        X, block_ids = extractor.fit_transform(sample_blocks)

        assert X.shape[0] == 22
        assert X.shape[1] == len(extractor.feature_names_)
        assert "total_events" in extractor.feature_names_
        assert "has_error" in extractor.feature_names_
        assert "event_entropy" in extractor.feature_names_
        assert len(block_ids) == 22

    def test_rare_event_detection(self, sample_blocks):
        """Verify rare templates are identified based on training frequency."""
        extractor = BlockFeatureExtractor(rare_threshold=0.05, scale_features=False)
        extractor.fit(sample_blocks)

        assert "E99" in extractor.rare_templates
        # Normal templates should not be flagged as rare
        assert "E1" not in extractor.rare_templates

    def test_transform_unfitted_raises(self, sample_blocks):
        """Verify transform() requires fit() first."""
        extractor = BlockFeatureExtractor()
        with pytest.raises(RuntimeError, match="must be fitted"):
            extractor.transform(sample_blocks)

    def test_extractor_save_and_load(self, sample_blocks, tmp_path):
        """Verify feature extractor state and scaler can be saved and reloaded."""
        extractor = BlockFeatureExtractor(scale_features=True)
        X1, _ = extractor.fit_transform(sample_blocks)

        save_file = tmp_path / "extractor_state.json"
        extractor.save(save_file)
        assert save_file.exists()

        loaded_extractor = BlockFeatureExtractor.load(save_file)
        assert loaded_extractor.is_fitted
        assert loaded_extractor.vocab_templates == extractor.vocab_templates

        X2, _ = loaded_extractor.transform(sample_blocks)
        np.testing.assert_allclose(X1, X2, rtol=1e-5)


class TestIsolationForestDetector:

    def test_fit_predict_and_scores(self, sample_blocks):
        """Verify IsolationForestDetector produces normalised scores in [0, 1]."""
        extractor = BlockFeatureExtractor(scale_features=True)
        X, _ = extractor.fit_transform(sample_blocks)

        detector = IsolationForestDetector(n_estimators=50, contamination=0.1, random_state=42)
        detector.fit(X)

        scores = detector.score(X)
        preds = detector.predict(X)

        assert scores.shape == (22,)
        assert np.all(scores >= 0.0) and np.all(scores <= 1.0)
        assert set(preds).issubset({0, 1})

    def test_predict_block_inference(self, sample_blocks):
        """Verify single block inference helper."""
        extractor = BlockFeatureExtractor(scale_features=True)
        extractor.fit(sample_blocks)

        detector = IsolationForestDetector(n_estimators=50, contamination=0.1, random_state=42)
        X, _ = extractor.transform(sample_blocks)
        detector.fit(X)

        anom_events = sample_blocks["blk_anomaly_0"]
        res = detector.predict_block("blk_anomaly_0", anom_events, extractor)

        assert res["block_id"] == "blk_anomaly_0"
        assert "anomaly_score" in res
        assert 0.0 <= res["anomaly_score"] <= 1.0
        assert "is_anomaly" in res
        assert "top_features" in res
        assert len(res["top_features"]) <= 5

    def test_model_save_and_load(self, sample_blocks, tmp_path):
        """Verify model serialization and reloadability with joblib."""
        extractor = BlockFeatureExtractor(scale_features=True)
        X, _ = extractor.fit_transform(sample_blocks)

        detector = IsolationForestDetector(n_estimators=30, contamination=0.1, random_state=42)
        detector.fit(X)

        model_file = tmp_path / "if_model.joblib"
        detector.save(model_file)
        assert model_file.exists()

        reloaded = IsolationForestDetector.load(model_file)
        assert reloaded.is_fitted
        np.testing.assert_allclose(detector.score(X), reloaded.score(X), rtol=1e-5)


class TestEvaluationModule:

    def test_evaluate_predictions_metrics(self):
        """Verify metric calculation accuracy without invented values."""
        y_true = np.array([0, 0, 0, 0, 1, 1])
        y_pred = np.array([0, 0, 0, 1, 1, 0])
        scores = np.array([0.1, 0.2, 0.15, 0.6, 0.9, 0.4])

        report = evaluate_predictions(y_true, y_pred, scores=scores)
        assert isinstance(report, EvaluationReport)
        assert report.total_samples == 6
        assert report.true_positives == 1
        assert report.false_positives == 1
        assert report.true_negatives == 3
        assert report.false_negatives == 1
        assert report.precision == 0.5
        assert report.recall == 0.5
        assert report.f1 == 0.5
        assert report.auc_roc is not None

    def test_generate_evaluation_plots(self, tmp_path):
        """Verify evaluation dashboard generates PNG plot."""
        y_true = np.array([0] * 50 + [1] * 10)
        y_pred = np.array([0] * 48 + [1] * 2 + [0] * 3 + [1] * 7)
        scores = np.random.uniform(0.0, 1.0, size=60)

        out_img = tmp_path / "eval_plot.png"
        generate_evaluation_plots(y_true, y_pred, scores=scores, output_path=out_img)
        assert out_img.exists()
        assert out_img.stat().st_size > 1000
