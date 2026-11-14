"""
Window builder — groups parsed log results into fixed or sliding windows.

Each window becomes one "sample" for the anomaly detector.
"""
from __future__ import annotations

from typing import List

from ml.parser.drain_parser import ParseResult


class WindowBuilder:
    """
    Groups a list of ParseResult objects into windows of `size` lines.

    Args:
        size:   Window size (number of log lines per sample).
        step:   Step between consecutive windows (1 = fully sliding).
    """

    def __init__(self, size: int = 20, step: int = 20):
        if size <= 0 or step <= 0:
            raise ValueError("size and step must be positive integers")
        self.size = size
        self.step = step

    def build(self, results: List[ParseResult]) -> List[List[ParseResult]]:
        """Return a list of windows (each window = list of ParseResults)."""
        windows: List[List[ParseResult]] = []
        i = 0
        while i < len(results):
            window = results[i : i + self.size]
            if window:
                windows.append(window)
            i += self.step
        return windows

    def flatten_templates(self, windows: List[List[ParseResult]]) -> List[List[str]]:
        """Return template sequences per window (useful for sequence models)."""
        return [[r.template for r in w] for w in windows]
