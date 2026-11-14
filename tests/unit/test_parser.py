"""Unit tests for the Drain3 log parser."""
from __future__ import annotations

import pytest

from ml.parser.drain_parser import DrainParser, ParseResult
from ml.parser.log_loader import load_lines


class TestDrainParser:
    def setup_method(self):
        self.parser = DrainParser()

    def test_parse_returns_result(self):
        result = self.parser.parse("081109 203615 148 INFO dfs.DataNode: Receiving block blk_123")
        assert isinstance(result, ParseResult)
        assert result.template
        assert result.template_id

    def test_same_template_for_similar_lines(self):
        lines = [
            "Receiving block blk_111 from /10.0.0.1",
            "Receiving block blk_222 from /10.0.0.2",
            "Receiving block blk_333 from /10.0.0.3",
        ]
        results = [self.parser.parse(l) for l in lines]
        # All should map to the same template cluster
        ids = {r.template_id for r in results}
        assert len(ids) == 1, f"Expected 1 template cluster, got {ids}"

    def test_different_templates_for_different_lines(self):
        r1 = self.parser.parse("Connection accepted from /10.0.0.1 port 22")
        r2 = self.parser.parse("Disk I/O error on device /dev/sda1")
        # These should produce different templates
        assert r1.template_id != r2.template_id

    def test_parse_lines_batch(self):
        lines = [
            "ERROR block blk_100 is corrupt",
            "INFO  block blk_200 replicated",
            "WARN  block blk_300 missing",
        ]
        results = self.parser.parse_lines(lines)
        assert len(results) == 3
        for r in results:
            assert r.raw_line
            assert r.template

    def test_parse_lines_skips_empty(self):
        results = self.parser.parse_lines(["", "   ", "real line here", ""])
        assert len(results) == 1

    def test_get_templates_returns_dict(self):
        self.parser.parse("disk error on node 1")
        self.parser.parse("disk error on node 2")
        templates = self.parser.get_templates()
        assert isinstance(templates, dict)
        assert len(templates) >= 1


class TestLogLoader:
    def test_load_raw_string(self):
        blob = "line one\nline two\nline three"
        lines = load_lines(blob, fmt="raw")
        assert lines == ["line one", "line two", "line three"]

    def test_load_hdfs_format(self):
        blob = (
            "081109 203615 148 INFO dfs.DataNode$DataXceiver: Receiving block blk_123\n"
            "081109 203616 148 ERROR dfs.FSNamesystem: Corrupt block blk_456\n"
        )
        lines = load_lines(blob, fmt="hdfs")
        assert len(lines) == 2
        assert "Receiving block" in lines[0]
        assert "Corrupt block" in lines[1]

    def test_load_syslog_format(self):
        blob = (
            "Nov 14 10:00:01 host sshd[1234]: Accepted publickey for user1\n"
            "Nov 14 10:00:05 host kernel: OOM kill process 999\n"
        )
        lines = load_lines(blob, fmt="syslog")
        assert len(lines) == 2

    def test_max_lines_limit(self):
        blob = "\n".join(f"line {i}" for i in range(100))
        lines = load_lines(blob, fmt="raw", max_lines=10)
        assert len(lines) == 10

    def test_load_actual_hdfs_file(self):
        lines = load_lines("data/raw/sample_hdfs.log", fmt="hdfs")
        assert len(lines) > 0
