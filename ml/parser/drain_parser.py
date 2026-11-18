"""
LogSage Drain3 Log Parsing Engine.

Features:
- Configured via parser_config.ini (Drain parameters, regex masks, delimiters).
- Extracts Event IDs (e.g. E1, E2) and Event Templates.
- Extracts timestamps (HDFS YYMMDD HHMMSS, ISO-8601, syslog).
- Extracts Block IDs (blk_-?\\d+).
- Extracts variable parameters via Drain3 parameter extraction.
- Preserves complete original log lines without mutation.
- Supports both incremental online streaming parsing and batch processing.
- Handles malformed, truncated, or non-standard records gracefully.
- Exports structured records to JSON / CSV compatible with ML and FastAPI.
"""
from __future__ import annotations

import csv
import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

import pandas as pd
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig

from backend.core.logging import get_logger

logger = get_logger(__name__)

# Regular expressions for header parsing & metadata extraction
BLOCK_ID_REGEX = re.compile(r"(blk_-?\d+)")

HDFS_HEADER_REGEX = re.compile(
    r"^(?P<date>\d{6})\s+(?P<time>\d{6})\s+(?P<pid>\d+)\s+(?P<level>[A-Z]+)\s+(?P<component>[^:]+):\s+(?P<content>.*)$"
)

SYSLOG_HEADER_REGEX = re.compile(
    r"^(?P<month>[A-Za-z]{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+(?P<host>\S+)\s+(?P<component>[^:\[]+)(?:\[(?P<pid>\d+)\])?:\s+(?P<content>.*)$"
)

ISO_TIMESTAMP_REGEX = re.compile(
    r"\b(?P<iso>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)\b"
)


@dataclass
class ParseResult:
    """Structured record produced by the Drain3 parsing engine."""
    line_id: int
    raw_message: str
    event_id: str
    event_template: str
    content: str
    timestamp: Optional[str] = None
    level: Optional[str] = None
    component: Optional[str] = None
    pid: Optional[int] = None
    block_ids: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    parameter_details: List[Dict[str, str]] = field(default_factory=list)
    is_new_template: bool = False
    is_malformed: bool = False
    malformed_reason: Optional[str] = None

    # Backward compatibility aliases
    @property
    def raw_line(self) -> str:
        return self.raw_message

    @property
    def template(self) -> str:
        return self.event_template

    @property
    def template_id(self) -> str:
        return self.event_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary schema compatible with FastAPI and ML pipelines."""
        return {
            "line_id": self.line_id,
            "raw_message": self.raw_message,
            "timestamp": self.timestamp,
            "level": self.level,
            "component": self.component,
            "pid": self.pid,
            "event_id": self.event_id,
            "event_template": self.event_template,
            "content": self.content,
            "block_ids": self.block_ids,
            "parameters": self.parameters,
            "parameter_details": self.parameter_details,
            "is_new_template": self.is_new_template,
            "is_malformed": self.is_malformed,
            "malformed_reason": self.malformed_reason,
        }


def _load_config(config_path: Optional[str | Path] = None) -> TemplateMinerConfig:
    """Load Drain3 configuration from file, falling back to default configuration."""
    cfg = TemplateMinerConfig()

    search_paths = []
    if config_path:
        search_paths.append(Path(config_path))
    search_paths.extend([
        Path("ml/parser/parser_config.ini"),
        Path(__file__).parent / "parser_config.ini",
        Path("parser_config.ini"),
    ])

    loaded = False
    for p in search_paths:
        if p.exists():
            cfg.load(str(p))
            # Workaround for Drain3 string-parsing bug in parameter_extraction_cache_capacity
            if hasattr(cfg, "parameter_extraction_cache_capacity"):
                try:
                    cfg.parameter_extraction_cache_capacity = int(cfg.parameter_extraction_cache_capacity)
                except (ValueError, TypeError):
                    cfg.parameter_extraction_cache_capacity = 3000
            loaded = True
            logger.info("Loaded Drain3 configuration", path=str(p))
            break

    if not loaded:
        logger.info("Using built-in default Drain3 configuration")
        cfg.drain_depth = 4
        cfg.drain_sim_th = 0.5
        cfg.drain_max_children = 100
        cfg.drain_extra_delimiters = []
        cfg.parametrize_numeric_tokens = True

    return cfg


class DrainParser:
    """LogSage Drain3 Parsing Engine."""

    def __init__(self, config_path: Optional[str | Path] = None, state_path: Optional[str] = None):
        self._config_path = config_path
        self._state_path = state_path
        self.config = _load_config(config_path)
        self._miner = TemplateMiner(config=self.config)
        self._line_counter: int = 0
        self._loaded_templates: Dict[str, str] = {}
        logger.info(
            "DrainParser initialised",
            depth=self.config.drain_depth,
            sim_th=self.config.drain_sim_th,
        )

    # ── Header and Metadata Parsing ──────────────────────────────────────────

    def extract_header_and_content(self, line: str) -> Tuple[Dict[str, Any], bool, Optional[str]]:
        """
        Parses structured headers (HDFS or syslog) and separates them from payload content.
        Returns:
            (metadata_dict, is_malformed, malformed_reason)
        """
        stripped = line.strip()
        if not stripped:
            return {}, True, "Empty log line"

        # Check HDFS format: 081109 203615 148 INFO dfs.DataNode$DataXceiver: ...
        m_hdfs = HDFS_HEADER_REGEX.match(stripped)
        if m_hdfs:
            d = m_hdfs.groupdict()
            # Standardise timestamp: YYMMDD HHMMSS -> YYYY-MM-DD HH:MM:SS
            raw_date = d["date"]
            raw_time = d["time"]
            formatted_ts = f"20{raw_date[0:2]}-{raw_date[2:4]}-{raw_date[4:6]} {raw_time[0:2]}:{raw_time[2:4]}:{raw_time[4:6]}"
            try:
                pid = int(d["pid"])
            except ValueError:
                pid = None

            return {
                "timestamp": formatted_ts,
                "level": d["level"],
                "component": d["component"].strip(),
                "pid": pid,
                "content": d["content"].strip(),
            }, False, None

        # Check syslog format
        m_syslog = SYSLOG_HEADER_REGEX.match(stripped)
        if m_syslog:
            d = m_syslog.groupdict()
            pid = int(d["pid"]) if d.get("pid") else None
            return {
                "timestamp": f"{d['month']} {d['day']} {d['time']}",
                "level": "INFO",
                "component": d["component"].strip(),
                "pid": pid,
                "content": d["content"].strip(),
            }, False, None

        # Check ISO timestamp in arbitrary log line
        m_iso = ISO_TIMESTAMP_REGEX.search(stripped)
        timestamp = m_iso.group("iso") if m_iso else None

        # Line without recognized header
        return {
            "timestamp": timestamp,
            "level": None,
            "component": None,
            "pid": None,
            "content": stripped,
        }, False, None

    # ── Core Parsing API ───────────────────────────────────────────────────

    def parse(self, line: str, line_id: Optional[int] = None, update_model: bool = True) -> ParseResult:
        """
        Parse a single log message.

        Args:
            line: Raw log line string.
            line_id: Optional manual line sequence ID.
            update_model: If True, incrementally updates Drain3 clusters.

        Returns:
            ParseResult object with extracted templates, parameters, and metadata.
        """
        self._line_counter += 1
        current_id = line_id if line_id is not None else self._line_counter

        raw_line = line.rstrip("\r\n")
        if not raw_line.strip():
            return ParseResult(
                line_id=current_id,
                raw_message=raw_line,
                event_id="E0",
                event_template="<EMPTY>",
                content="",
                is_malformed=True,
                malformed_reason="Empty log line",
            )

        meta, is_malformed, malformed_reason = self.extract_header_and_content(raw_line)
        content = meta.get("content", raw_line)
        block_ids = BLOCK_ID_REGEX.findall(raw_line)

        # Incrementally parse content with Drain3
        try:
            if update_model:
                result = self._miner.add_log_message(content)
                event_template = result["template_mined"]
                cluster_id = result["cluster_id"]
                is_new = (result["change_type"] == "cluster_created")
            else:
                cluster = self._miner.match(content)
                if cluster:
                    event_template = cluster.get_template()
                    cluster_id = cluster.cluster_id
                    is_new = False
                else:
                    event_template = content
                    cluster_id = 0
                    is_new = False

            event_id = f"E{cluster_id}"

            # Extract variable parameters
            params: List[str] = []
            param_details: List[Dict[str, str]] = []
            try:
                extracted = self._miner.extract_parameters(event_template, content, exact_matching=False)
                if extracted:
                    for p in extracted:
                        params.append(p.value)
                        param_details.append({
                            "value": p.value,
                            "mask_name": getattr(p, "mask_name", "VAR"),
                        })
            except Exception:
                pass

        except Exception as exc:
            # Gracefully handle unexpected parse exceptions
            is_malformed = True
            malformed_reason = f"Drain3 parsing error: {exc}"
            event_id = "E_ERR"
            event_template = content
            params = []
            param_details = []
            is_new = False

        return ParseResult(
            line_id=current_id,
            raw_message=raw_line,
            event_id=event_id,
            event_template=event_template,
            content=content,
            timestamp=meta.get("timestamp"),
            level=meta.get("level"),
            component=meta.get("component"),
            pid=meta.get("pid"),
            block_ids=block_ids,
            parameters=params,
            parameter_details=param_details,
            is_new_template=is_new,
            is_malformed=is_malformed,
            malformed_reason=malformed_reason,
        )

    def parse_lines(
        self,
        lines: Union[List[str], Iterator[str]],
        update_model: bool = True,
        skip_empty: bool = True,
    ) -> List[ParseResult]:
        """Batch process a collection of log lines."""
        results: List[ParseResult] = []
        for line in lines:
            if skip_empty and not line.strip():
                continue
            results.append(self.parse(line, update_model=update_model))
        return results

    def parse_file(
        self,
        filepath: str | Path,
        max_lines: Optional[int] = None,
        update_model: bool = True,
    ) -> Iterator[ParseResult]:
        """Streams parsed records from a file on disk."""
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Log file not found: {filepath}")

        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for idx, line in enumerate(f, start=1):
                if max_lines and idx > max_lines:
                    break
                yield self.parse(line, line_id=idx, update_model=update_model)

    # ── State and Template Management ──────────────────────────────────────

    def get_templates(self) -> Dict[str, str]:
        """Return all mined templates as {event_id: template_string}."""
        miner_templates = {
            f"E{c.cluster_id}": c.get_template()
            for c in self._miner.drain.id_to_cluster.values()
        }
        if miner_templates:
            return miner_templates
        return dict(self._loaded_templates)

    def get_cluster_stats(self) -> Dict[str, Dict[str, Any]]:
        """Return statistics for each mined cluster."""
        return {
            f"E{c.cluster_id}": {
                "template": c.get_template(),
                "size": c.size,
            }
            for c in self._miner.drain.id_to_cluster.values()
        }

    def save(self, path: Optional[str | Path] = None) -> None:
        """Save parser state and mined templates to a JSON snapshot."""
        save_path = Path(path or self._state_path or "ml/models/saved/drain_state.json")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "templates": self.get_templates(),
            "cluster_stats": self.get_cluster_stats(),
            "total_lines_parsed": self._line_counter,
            "config": {
                "depth": self.config.drain_depth,
                "sim_th": self.config.drain_sim_th,
                "max_children": self.config.drain_max_children,
            },
        }
        save_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        logger.info("DrainParser state saved", path=str(save_path))

    @classmethod
    def load(cls, path: str | Path, config_path: Optional[str | Path] = None) -> "DrainParser":
        """Load parser snapshot from disk."""
        path = Path(path)
        parser = cls(config_path=config_path, state_path=str(path))
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            parser._line_counter = data.get("total_lines_parsed", 0)
            parser._loaded_templates = data.get("templates", {})
            logger.info("Loaded DrainParser snapshot", path=str(path), templates=len(parser._loaded_templates))
        return parser

    # ── Data Export Utilities ──────────────────────────────────────────────

    @staticmethod
    def to_dataframe(results: List[ParseResult]) -> pd.DataFrame:
        """Convert a list of ParseResult objects to a pandas DataFrame."""
        records = [r.to_dict() for r in results]
        return pd.DataFrame(records)

    @staticmethod
    def to_csv(results: List[ParseResult], output_path: str | Path) -> None:
        """Save parsed records to a structured CSV file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df = DrainParser.to_dataframe(results)
        # Convert lists to JSON strings for clean CSV serialization
        df["block_ids"] = df["block_ids"].apply(json.dumps)
        df["parameters"] = df["parameters"].apply(json.dumps)
        df["parameter_details"] = df["parameter_details"].apply(json.dumps)
        df.to_csv(output_path, index=False, encoding="utf-8")
        logger.info("Saved structured CSV", path=str(output_path), rows=len(df))

    @staticmethod
    def to_json(results: List[ParseResult], output_path: str | Path, indent: int = 2) -> None:
        """Save parsed records to a structured JSON file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = [r.to_dict() for r in results]
        output_path.write_text(json.dumps(data, indent=indent, ensure_ascii=False), encoding="utf-8")
        logger.info("Saved structured JSON", path=str(output_path), records=len(data))
