"""Regression coverage for deployment-configured model artifact locations."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.services import pipeline_service as pipeline_module
from ml.logfit_training import DEFAULT_ARTIFACT_DIR


@pytest.mark.parametrize("include_native_parser_state", [True, False])
def test_pipeline_uses_configured_model_dir_and_requires_native_parser_state(
    tmp_path: Path,
    monkeypatch,
    include_native_parser_state: bool,
):
    artifact_dir = tmp_path / "release-2026-11"
    artifact_dir.mkdir()
    model_path = artifact_dir / "isolation_forest.joblib"
    extractor_path = artifact_dir / "feature_extractor.json"
    parser_path = artifact_dir / "drain_state.json"
    native_parser_path = artifact_dir / "drain_state.bin"
    for path in (model_path, extractor_path, parser_path):
        path.touch()
    if include_native_parser_state:
        native_parser_path.touch()

    detector = SimpleNamespace(is_fitted=True)
    extractor = SimpleNamespace(is_fitted=True)
    loaded_paths: dict[str, Path] = {}
    parser = object()

    def load_parser(path, config_path=None):
        loaded_paths["parser"] = Path(path)
        return parser

    def load_detector(path):
        loaded_paths["model"] = Path(path)
        return detector

    def load_extractor(path):
        loaded_paths["extractor"] = Path(path)
        return extractor

    monkeypatch.setattr(pipeline_module.settings, "MODEL_SAVE_DIR", str(artifact_dir))
    monkeypatch.setattr(pipeline_module.DrainParser, "load", load_parser)
    monkeypatch.setattr(pipeline_module.IsolationForestDetector, "load", staticmethod(load_detector))
    monkeypatch.setattr(pipeline_module.BlockFeatureExtractor, "load", staticmethod(load_extractor))

    service = pipeline_module.PipelineService()

    assert loaded_paths == {
        "parser": parser_path,
        "model": model_path,
        "extractor": extractor_path,
    }
    assert service.is_ml_ready is include_native_parser_state
    assert service.parser_state_loaded is include_native_parser_state
    assert service.parser is parser


def test_training_default_artifact_dir_matches_runtime_setting():
    assert DEFAULT_ARTIFACT_DIR == Path(pipeline_module.settings.MODEL_SAVE_DIR)
