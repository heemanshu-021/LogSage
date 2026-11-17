"""
Drain3 log template parser wrapper.

Wraps the drain3.TemplateMiner to provide:
  - add_log_message()   → returns (template, template_id, is_new)
  - parse_lines()       → batch helper
  - save() / load()     → persist the miner state to disk
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig

from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ParseResult:
    raw_line: str
    template: str
    template_id: str
    parameters: List[str] = field(default_factory=list)
    is_new_template: bool = False


def _build_drain_config() -> TemplateMinerConfig:
    cfg = TemplateMinerConfig()
    cfg.drain_depth = settings.DRAIN_DEPTH
    cfg.drain_sim_th = settings.DRAIN_SIM_TH
    cfg.drain_max_children = settings.DRAIN_MAX_CHILDREN
    cfg.parametrize_numeric_tokens = True
    return cfg


class DrainParser:
    """Thread-safe (single-process) Drain3 wrapper."""

    def __init__(self, state_path: Optional[str] = None):
        self._state_path = state_path
        cfg = _build_drain_config()
        self._miner = TemplateMiner(config=cfg)
        logger.info(
            "DrainParser initialised",
            depth=cfg.drain_depth,
            sim_th=cfg.drain_sim_th,
        )

    # ── Public API ─────────────────────────────────────────────────────────

    def parse(self, line: str) -> ParseResult:
        """Parse a single log line and return a ParseResult."""
        line = line.strip()
        result = self._miner.add_log_message(line)
        return ParseResult(
            raw_line=line,
            template=result["template_mined"],
            template_id=str(result["cluster_id"]),
            parameters=[],
            is_new_template=result["change_type"] == "cluster_created",
        )

    def parse_lines(self, lines: List[str]) -> List[ParseResult]:
        """Parse a list of log lines."""
        results = []
        for line in lines:
            if line.strip():
                results.append(self.parse(line))
        return results

    def get_templates(self) -> dict:
        """Return all current templates as {template_id: template_string}."""
        return {
            str(c.cluster_id): c.get_template()
            for c in self._miner.drain.id_to_cluster.values()
        }

    # ── Persistence ────────────────────────────────────────────────────────

    def save(self, path: Optional[str] = None) -> None:
        save_path = Path(path or self._state_path or "ml/models/saved/drain_state.json")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "templates": self.get_templates(),
            "config": {
                "depth": settings.DRAIN_DEPTH,
                "sim_th": settings.DRAIN_SIM_TH,
            },
        }
        save_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        logger.info("DrainParser state saved", path=str(save_path))

    @classmethod
    def load(cls, path: str) -> "DrainParser":
        """Load a parser (creates fresh miner; replays not supported yet)."""
        logger.info("DrainParser loading from", path=path)
        return cls(state_path=path)
