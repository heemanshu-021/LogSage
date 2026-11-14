"""Unit tests for feature extraction and window builder."""
from __future__ import annotations

import numpy as np
import pytest

from ml.parser.drain_parser import DrainParser, ParseResult
from ml.preprocessing.feature_extractor import FeatureExtractor
from ml.preprocessing.window_builder import WindowBuilder


def _make_results(n: int = 30) -> list[ParseResult]:
    parser = DrainParser()
    lines = (
        [f"Receiving block blk_{i} from /10.0.0.{i%10}" for i in range(n // 3)]
        + [f"ERROR block blk_{i} is corrupt" for i in range(n // 3)]
        + [f"Connection timeout retries={i}" for i in range(n // 3)]
    )
    return parser.parse_lines(lines)


class TestFeatureExtractor:
    def test_fit_transform_shape(self):
        results = _make_results(30)
        fe = FeatureExtractor(max_tfidf_features=50)
        X = fe.fit_transform(results)
        assert X.shape == (len(results), fe.feature_dim)

    def test_transform_without_fit_raises(self):
        results = _make_results(10)
        fe = FeatureExtractor()
        with pytest.raises(RuntimeError, match="fit\\(\\)"):
            fe.transform(results)

    def test_error_lines_have_different_features(self):
        parser = DrainParser()
        normal = parser.parse_lines(["INFO receiving block blk_100"] * 10)
        error  = parser.parse_lines(["ERROR block blk_200 is corrupt"] * 10)

        fe = FeatureExtractor(max_tfidf_features=20)
        fe.fit(normal + error)
        X_normal = fe.transform(normal)
        X_error  = fe.transform(error)

        # error flag column (index -4) should differ
        assert X_error[:, -4].mean() != X_normal[:, -4].mean()

    def test_feature_dim_property(self):
        fe = FeatureExtractor(max_tfidf_features=30)
        assert fe.feature_dim == 34   # 30 TF-IDF + 4 hand-crafted


class TestWindowBuilder:
    def test_fixed_windows(self):
        results = _make_results(60)
        wb = WindowBuilder(size=20, step=20)
        windows = wb.build(results)
        assert len(windows) == 3
        for w in windows:
            assert len(w) <= 20

    def test_sliding_windows(self):
        results = _make_results(30)
        wb = WindowBuilder(size=10, step=5)
        windows = wb.build(results)
        # With 30 items, size=10, step=5: starts at 0,5,10,15,20,25 → 6 windows
        assert len(windows) == 6

    def test_flatten_templates(self):
        results = _make_results(20)
        wb = WindowBuilder(size=10, step=10)
        windows = wb.build(results)
        flat = wb.flatten_templates(windows)
        assert len(flat) == len(windows)
        for seq in flat:
            assert all(isinstance(t, str) for t in seq)

    def test_invalid_params(self):
        with pytest.raises(ValueError):
            WindowBuilder(size=0, step=10)
        with pytest.raises(ValueError):
            WindowBuilder(size=10, step=0)
