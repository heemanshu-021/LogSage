"""
HDFS Log Preprocessing Utilities.

CRITICAL SPECIFICATION:
- HDFS anomaly labels in LogHub are assigned at the BLOCK LEVEL (BlockId), NOT individual log lines.
- Original raw logs must be preserved without loss.
- Never randomly assign labels to individual lines.
- Malformed records (missing block IDs, corrupted lines, or unparseable formats) are isolated and handled gracefully.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Set, Tuple

import pandas as pd


# Regex for HDFS block identifier (e.g. blk_-1608999687919862906 or blk_7503483334202473044)
BLOCK_ID_REGEX = re.compile(r"(blk_-?\d+)")

# Standard HDFS log format: Date Time Pid Level Component Content
# Example: 081109 203615 148 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_38865049064139660 terminating
HDFS_LINE_REGEX = re.compile(
    r"^(?P<date>\d{6})\s+(?P<time>\d{6})\s+(?P<pid>\d+)\s+(?P<level>[A-Z]+)\s+(?P<component>[^:]+):\s+(?P<content>.*)$"
)


@dataclass
class HDFSLogRecord:
    """Represents a single parsed HDFS log record."""
    line_number: int
    raw_line: str
    date: Optional[str] = None
    time: Optional[str] = None
    pid: Optional[int] = None
    level: Optional[str] = None
    component: Optional[str] = None
    content: Optional[str] = None
    block_ids: List[str] = field(default_factory=list)
    is_malformed: bool = False
    malformed_reason: Optional[str] = None

    @property
    def primary_block_id(self) -> Optional[str]:
        """Returns the first block ID mentioned in the record, if any."""
        return self.block_ids[0] if self.block_ids else None


@dataclass
class BlockTrace:
    """Represents the ordered sequence of log records associated with a BlockId."""
    block_id: str
    records: List[HDFSLogRecord] = field(default_factory=list)
    label: Optional[str] = None  # 'Normal' | 'Anomaly' | None

    @property
    def event_count(self) -> int:
        return len(self.records)

    @property
    def has_error(self) -> bool:
        return any(r.level in ("ERROR", "FATAL", "CRITICAL") for r in self.records)

    @property
    def has_warning(self) -> bool:
        return any(r.level in ("WARN", "WARNING") for r in self.records)

    @property
    def components(self) -> Set[str]:
        return {r.component for r in self.records if r.component}


class HDFSPreprocessor:
    """Reusable preprocessor for LogHub HDFS logs and block-level labels."""

    def __init__(self, labels_path: Optional[str | Path] = None):
        self._labels: Dict[str, str] = {}
        if labels_path:
            self.load_labels(labels_path)

    def load_labels(self, path: str | Path) -> Dict[str, str]:
        """Load block labels from anomaly_label.csv into memory."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Labels file not found: {path}")

        df = pd.read_csv(path)
        if "BlockId" not in df.columns or "Label" not in df.columns:
            raise ValueError("CSV must contain 'BlockId' and 'Label' columns")

        self._labels = dict(zip(df["BlockId"], df["Label"]))
        return self._labels

    @property
    def label_count(self) -> int:
        return len(self._labels)

    def parse_line(self, line: str, line_number: int = 0) -> HDFSLogRecord:
        """
        Parses an individual HDFS log line, extracting fields and all block IDs.
        Handles malformed or non-standard records gracefully.
        """
        stripped = line.rstrip("\r\n")
        if not stripped.strip():
            return HDFSLogRecord(
                line_number=line_number,
                raw_line=stripped,
                is_malformed=True,
                malformed_reason="Empty line",
            )

        match = HDFS_LINE_REGEX.match(stripped)
        block_ids = BLOCK_ID_REGEX.findall(stripped)

        if match:
            group = match.groupdict()
            try:
                pid = int(group["pid"])
            except ValueError:
                pid = None

            return HDFSLogRecord(
                line_number=line_number,
                raw_line=stripped,
                date=group["date"],
                time=group["time"],
                pid=pid,
                level=group["level"],
                component=group["component"].strip(),
                content=group["content"],
                block_ids=block_ids,
                is_malformed=(len(block_ids) == 0),
                malformed_reason="No BlockId found" if len(block_ids) == 0 else None,
            )
        else:
            # Fallback for lines that don't match standard header (e.g., stack trace continuation)
            return HDFSLogRecord(
                line_number=line_number,
                raw_line=stripped,
                block_ids=block_ids,
                is_malformed=True,
                malformed_reason="Malformed line header format",
            )

    def parse_file(
        self,
        filepath: str | Path,
        max_lines: Optional[int] = None,
    ) -> Iterator[HDFSLogRecord]:
        """Streams parsed records from a log file."""
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Log file not found: {filepath}")

        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for idx, line in enumerate(f, start=1):
                if max_lines and idx > max_lines:
                    break
                yield self.parse_line(line, line_number=idx)

    def group_by_block(
        self,
        records: Iterator[HDFSLogRecord] | List[HDFSLogRecord],
    ) -> Tuple[Dict[str, BlockTrace], List[HDFSLogRecord]]:
        """
        Groups log records by their BlockId into BlockTrace objects.
        
        Returns:
            (block_traces_dict, unassigned_records_list)
        """
        traces: Dict[str, BlockTrace] = {}
        unassigned: List[HDFSLogRecord] = []

        for rec in records:
            if not rec.block_ids:
                unassigned.append(rec)
                continue

            for b_id in rec.block_ids:
                if b_id not in traces:
                    label = self._labels.get(b_id)
                    traces[b_id] = BlockTrace(block_id=b_id, label=label)
                traces[b_id].records.append(rec)

        return traces, unassigned

    def to_dataframe(
        self,
        block_traces: Dict[str, BlockTrace],
    ) -> pd.DataFrame:
        """
        Converts aggregated block traces into a summary DataFrame suitable for EDA and ML.
        Preserves block-level granularity.
        """
        data = []
        for b_id, trace in block_traces.items():
            level_counts = {}
            for r in trace.records:
                lvl = r.level or "UNKNOWN"
                level_counts[lvl] = level_counts.get(lvl, 0) + 1

            data.append({
                "BlockId": b_id,
                "EventCount": trace.event_count,
                "Label": trace.label or "Unknown",
                "IsAnomaly": 1 if trace.label == "Anomaly" else (0 if trace.label == "Normal" else -1),
                "HasError": int(trace.has_error),
                "HasWarning": int(trace.has_warning),
                "NumComponents": len(trace.components),
                "InfoCount": level_counts.get("INFO", 0),
                "WarnCount": level_counts.get("WARN", 0),
                "ErrorCount": level_counts.get("ERROR", 0),
            })

        return pd.DataFrame(data)
