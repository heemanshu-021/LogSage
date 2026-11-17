"""Unit tests for HDFSPreprocessor utility."""
import pytest
from ml.preprocessing.hdfs_preprocessor import (
    HDFSPreprocessor,
    HDFSLogRecord,
    BLOCK_ID_REGEX,
)


def test_block_id_regex():
    line1 = "Receiving block blk_-1608999687919862906 src: /10.250.10.6"
    line2 = "addStoredBlock: 10.250.10.6 is added to blk_7503483334202473044"
    line3 = "Replicating blk_123 to blk_456"
    assert BLOCK_ID_REGEX.findall(line1) == ["blk_-1608999687919862906"]
    assert BLOCK_ID_REGEX.findall(line2) == ["blk_7503483334202473044"]
    assert BLOCK_ID_REGEX.findall(line3) == ["blk_123", "blk_456"]


def test_parse_valid_line():
    prep = HDFSPreprocessor()
    line = "081109 203615 148 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_38865049064139660 terminating"
    rec = prep.parse_line(line, line_number=1)
    assert not rec.is_malformed
    assert rec.date == "081109"
    assert rec.time == "203615"
    assert rec.pid == 148
    assert rec.level == "INFO"
    assert rec.component == "dfs.DataNode$PacketResponder"
    assert rec.primary_block_id == "blk_38865049064139660"


def test_parse_malformed_line():
    prep = HDFSPreprocessor()
    empty = prep.parse_line("", line_number=1)
    assert empty.is_malformed
    assert empty.malformed_reason == "Empty line"

    no_block = prep.parse_line("081109 203615 148 INFO dfs.DataNode: System starting up", line_number=2)
    assert no_block.is_malformed
    assert "No BlockId found" in (no_block.malformed_reason or "")


def test_group_by_block_and_labels(tmp_path):
    labels_file = tmp_path / "test_labels.csv"
    labels_file.write_text("BlockId,Label\nblk_101,Normal\nblk_102,Anomaly\n")

    prep = HDFSPreprocessor(labels_path=labels_file)
    assert prep.label_count == 2

    lines = [
        "081109 203615 148 INFO dfs.DataNode: Receiving block blk_101",
        "081109 203616 148 INFO dfs.DataNode: Received block blk_101",
        "081109 203617 148 ERROR dfs.DataNode: Corrupt block blk_102",
        "081109 203618 148 INFO dfs.DataNode: System heartbeat without block",
    ]
    records = [prep.parse_line(l, idx) for idx, l in enumerate(lines, 1)]
    traces, unassigned = prep.group_by_block(records)

    assert "blk_101" in traces
    assert traces["blk_101"].event_count == 2
    assert traces["blk_101"].label == "Normal"
    assert not traces["blk_101"].has_error

    assert "blk_102" in traces
    assert traces["blk_102"].event_count == 1
    assert traces["blk_102"].label == "Anomaly"
    assert traces["blk_102"].has_error

    assert len(unassigned) == 1
    assert unassigned[0].is_malformed

    df = prep.to_dataframe(traces)
    assert len(df) == 2
    assert set(df["Label"]) == {"Normal", "Anomaly"}
