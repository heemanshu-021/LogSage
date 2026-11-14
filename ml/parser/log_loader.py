"""
Log file loader — supports HDFS, syslog, and raw/custom formats.

Returns an iterator of raw log line strings.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator, List, Literal

LogFormat = Literal["hdfs", "syslog", "raw"]

# HDFS line pattern: 081109 203615 148 INFO dfs.DataNode$DataXceiver: ...
_HDFS_RE = re.compile(
    r"^(?P<date>\d{6})\s+(?P<time>\d{6})\s+(?P<pid>\d+)\s+(?P<level>\w+)\s+(?P<component>\S+):\s+(?P<content>.+)$"
)

# Syslog: Nov 14 10:00:01 hostname service[pid]: message
_SYSLOG_RE = re.compile(
    r"^(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>[\d:]+)\s+(?P<host>\S+)\s+(?P<service>\S+?):\s+(?P<content>.+)$"
)


def _iter_file(path: Path) -> Iterator[str]:
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\n\r")
            if line.strip():
                yield line


def load_lines(
    source: str | Path,
    fmt: LogFormat = "raw",
    max_lines: int = 0,
) -> List[str]:
    """
    Load log lines from a file path or a raw string blob.

    Args:
        source: Path to a log file, or a multi-line string.
        fmt:    'hdfs' | 'syslog' | 'raw'
        max_lines: 0 = no limit

    Returns:
        List of extracted content strings.
    """
    path = Path(source) if isinstance(source, str) and Path(source).exists() else None

    raw_lines: List[str] = []
    if path and path.is_file():
        raw_lines = list(_iter_file(path))
    else:
        # Treat source as raw text blob
        raw_lines = str(source).splitlines()

    if max_lines > 0:
        raw_lines = raw_lines[:max_lines]

    if fmt == "raw":
        return [l for l in raw_lines if l.strip()]

    extractor = _HDFS_RE if fmt == "hdfs" else _SYSLOG_RE
    result: List[str] = []
    for line in raw_lines:
        m = extractor.match(line)
        result.append(m.group("content") if m else line)
    return [l for l in result if l.strip()]
