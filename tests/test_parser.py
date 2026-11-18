"""
Comprehensive unit tests for the LogSage Drain3 Log Parsing Engine.

Verifies:
1. Configuration loading from parser_config.ini
2. Event ID and Event Template extraction
3. Timestamp extraction (HDFS YYMMDD HHMMSS, ISO-8601, syslog)
4. Block ID extraction (blk_-?\\d+)
5. Variable parameter extraction with mask details
6. Preservation of raw original log lines
7. Batch processing and file streaming
8. Incremental online learning vs match-only inference
9. Malformed and corrupted log line handling
10. JSON and CSV structured export compatibility
11. Parser state persistence (save/load)
"""
import json
from pathlib import Path
import pytest
import pandas as pd

from ml.parser.drain_parser import DrainParser, ParseResult


@pytest.fixture
def parser():
    """Fixture returning a fresh DrainParser instance with parser_config.ini."""
    return DrainParser(config_path="ml/parser/parser_config.ini")


class TestDrainParserEngine:

    def test_config_loaded(self, parser):
        """Verify Drain3 config is loaded from parser_config.ini."""
        assert parser.config.drain_depth == 4
        assert parser.config.drain_sim_th == 0.5
        assert parser.config.drain_max_children == 100
        assert len(parser.config.masking_instructions) >= 3

    def test_parse_hdfs_line_structure(self, parser):
        """Verify HDFS line header, event template, timestamp, component, and event ID."""
        line = "081109 203615 148 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_38865049064139660 terminating"
        res = parser.parse(line)

        assert isinstance(res, ParseResult)
        assert res.raw_message == line
        assert res.raw_line == line
        assert res.timestamp == "2008-11-09 20:36:15"
        assert res.level == "INFO"
        assert res.component == "dfs.DataNode$PacketResponder"
        assert res.pid == 148
        assert res.event_id.startswith("E")
        assert "PacketResponder" in res.event_template
        assert "<ID>" in res.event_template or "blk" in res.event_template
        assert not res.is_malformed

    def test_block_id_extraction(self, parser):
        """Verify extraction of standard positive and negative Block IDs."""
        line1 = "081109 203615 148 INFO dfs.DataNode: Receiving block blk_-1608999687919862906"
        line2 = "081109 203615 148 INFO dfs.DataNode: Replicating blk_111 to blk_222"

        res1 = parser.parse(line1)
        res2 = parser.parse(line2)

        assert res1.block_ids == ["blk_-1608999687919862906"]
        assert res2.block_ids == ["blk_111", "blk_222"]

    def test_variable_parameter_extraction(self, parser):
        """Verify variable parameters and mask metadata are extracted correctly."""
        line = "081109 203615 148 INFO dfs.DataNode: Receiving block blk_99999 src: /10.250.10.6:54106 dest: /10.250.10.6:50010"
        res = parser.parse(line)

        assert len(res.parameters) >= 2
        assert "blk_99999" in res.parameters
        mask_names = [d.get("mask_name") for d in res.parameter_details]
        assert "ID" in mask_names or "IP" in mask_names

    def test_template_clustering(self, parser):
        """Verify similar log messages cluster to the same Event ID and Event Template."""
        lines = [
            "081109 203615 148 INFO dfs.DataNode: PacketResponder 1 for block blk_100 terminating",
            "081109 203616 148 INFO dfs.DataNode: PacketResponder 2 for block blk_200 terminating",
            "081109 203617 148 INFO dfs.DataNode: PacketResponder 3 for block blk_300 terminating",
        ]
        results = [parser.parse(l) for l in lines]
        event_ids = {r.event_id for r in results}
        templates = {r.event_template for r in results}

        assert len(event_ids) == 1, f"Expected 1 cluster, got {event_ids}"
        assert len(templates) == 1

    def test_different_events_different_ids(self, parser):
        """Verify semantically different messages map to distinct Event IDs."""
        r1 = parser.parse("081109 203615 148 INFO dfs.DataNode: Receiving block blk_100")
        r2 = parser.parse("081109 203616 148 ERROR dfs.FSNamesystem: Disk I/O failure on drive /dev/sda")

        assert r1.event_id != r2.event_id
        assert r1.event_template != r2.event_template

    def test_timestamp_extraction_variations(self, parser):
        """Verify parsing of different timestamp formats (HDFS, syslog, ISO)."""
        # HDFS format
        hdfs_res = parser.parse("081109 203615 148 INFO dfs.DataNode: Message")
        assert hdfs_res.timestamp == "2008-11-09 20:36:15"

        # Syslog format
        sys_res = parser.parse("Nov 14 10:00:01 web01 sshd[123]: Accepted key")
        assert sys_res.timestamp == "Nov 14 10:00:01"

        # ISO format
        iso_res = parser.parse("2026-11-18T10:15:30Z [ERROR] Service down")
        assert iso_res.timestamp == "2026-11-18T10:15:30Z"

    def test_raw_message_preserved(self, parser):
        """Verify original raw line is strictly preserved without mutation or truncation."""
        raw = "081109 203615 148 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_38865049064139660 terminating   "
        res = parser.parse(raw)
        assert res.raw_message == raw.rstrip("\r\n")

    def test_batch_processing(self, parser):
        """Verify parse_lines handles batches accurately."""
        batch = [
            "081109 203615 148 INFO dfs.DataNode: Block blk_10 verified",
            "081109 203616 148 INFO dfs.DataNode: Block blk_20 verified",
            "081109 203617 148 WARN dfs.DataNode: Block blk_30 slow read",
        ]
        results = parser.parse_lines(batch)
        assert len(results) == 3
        assert results[0].line_id == 1
        assert results[1].line_id == 2
        assert results[2].line_id == 3

    def test_incremental_vs_inference_only(self, parser):
        """Verify incremental cluster updates vs update_model=False match-only inference."""
        line = "081109 203615 148 INFO dfs.DataNode: Unique message blk_777"
        r1 = parser.parse(line, update_model=True)
        assert r1.is_new_template

        # Parse new pattern with update_model=False
        new_unseen = "081109 203615 148 INFO dfs.DataNode: Completely unseen pattern blk_888"
        r2 = parser.parse(new_unseen, update_model=False)
        assert not r2.is_new_template

    def test_malformed_records_handling(self, parser):
        """Verify empty lines, truncated headers, and corrupted lines are flagged gracefully."""
        # Empty line
        res_empty = parser.parse("")
        assert res_empty.is_malformed
        assert res_empty.malformed_reason == "Empty log line"

        # Line without block ID
        res_noblock = parser.parse("081109 203615 148 INFO dfs.DataNode: Daemon startup initialized")
        assert not res_noblock.is_malformed
        assert res_noblock.block_ids == []
        assert res_noblock.content == "Daemon startup initialized"

        # Corrupted line
        res_corrupt = parser.parse("CORRUPTED_RAW_STREAM_DATA_CHUNK")
        assert not res_corrupt.is_malformed
        assert res_corrupt.content == "CORRUPTED_RAW_STREAM_DATA_CHUNK"

    def test_export_to_json_and_csv(self, parser, tmp_path):
        """Verify structured JSON and CSV outputs are created and schema compatible."""
        lines = [
            "081109 203615 148 INFO dfs.DataNode: Receiving block blk_100",
            "081109 203616 148 ERROR dfs.DataNode: Corrupt block blk_200",
        ]
        results = parser.parse_lines(lines)

        csv_file = tmp_path / "test_out.csv"
        json_file = tmp_path / "test_out.json"

        DrainParser.to_csv(results, csv_file)
        DrainParser.to_json(results, json_file)

        assert csv_file.exists()
        assert json_file.exists()

        # Check CSV schema
        df = pd.read_csv(csv_file)
        expected_cols = {
            "line_id", "raw_message", "timestamp", "level", "component",
            "event_id", "event_template", "content", "block_ids", "parameters"
        }
        assert expected_cols.issubset(set(df.columns))
        assert len(df) == 2

        # Check JSON schema
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[0]["event_id"] == results[0].event_id
        assert data[1]["level"] == "ERROR"

    def test_state_save_and_load(self, parser, tmp_path):
        """Verify parser snapshot can be persisted and loaded."""
        parser.parse("081109 203615 148 INFO dfs.DataNode: Receiving block blk_100")
        state_file = tmp_path / "drain_state.json"
        parser.save(state_file)

        assert state_file.exists()
        loaded = DrainParser.load(state_file)
        assert len(loaded.get_templates()) >= 1
