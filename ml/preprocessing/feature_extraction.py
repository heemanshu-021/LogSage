"""
LogSage Block-Level Feature Extraction Pipeline.

Extracts numerical representations for log sequences grouped by BlockId:
- Total event count
- Unique template count
- Template frequencies (fixed vocabulary learned on training split)
- Rare event frequency (templates occurring with < threshold frequency in training split)
- Event sequence statistics (Shannon entropy, component diversity, duration span)
- Error and warning counts
- Standard scaling (fitted strictly on training split to prevent data leakage)

Compatible with both batch DataFrames and online ParseResult streaming.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from backend.core.logging import get_logger

logger = get_logger(__name__)

BLOCK_ID_REGEX = re.compile(r"(blk_-?\d+)")


@dataclass
class BlockFeatures:
    """Dataclass holding extracted numerical features for a single Block ID."""
    block_id: str
    total_events: int
    unique_templates: int
    error_count: int
    warn_count: int
    has_error: int
    has_warning: int
    component_count: int
    rare_event_count: int
    rare_event_ratio: float
    event_entropy: float
    template_counts: Dict[str, int] = field(default_factory=dict)
    feature_vector: Optional[np.ndarray] = None


class BlockFeatureExtractor:
    """
    Stateful feature extractor for HDFS block traces.
    
    Guarantees no data leakage:
    - Template vocabulary is learned strictly from training data.
    - Rare templates (freq < rare_threshold) are identified on training data.
    - StandardScaler is fitted strictly on training feature matrix.
    """

    def __init__(
        self,
        rare_threshold: float = 0.01,
        max_templates: Optional[int] = 50,
        scale_features: bool = True,
    ):
        self.rare_threshold = rare_threshold
        self.max_templates = max_templates
        self.scale_features = scale_features

        self.vocab_templates: List[str] = []
        self.rare_templates: Set[str] = set()
        self.feature_names_: List[str] = []
        self.scaler = StandardScaler() if scale_features else None
        self.is_fitted: bool = False

    # ── Internal Block Feature Calculation ──────────────────────────────────

    def _extract_single_block_features(
        self,
        block_id: str,
        events: Sequence[Dict[str, Any]],
    ) -> BlockFeatures:
        """Extract unscaled numerical summary for a single block."""
        total_events = len(events)
        if total_events == 0:
            return BlockFeatures(
                block_id=block_id,
                total_events=0,
                unique_templates=0,
                error_count=0,
                warn_count=0,
                has_error=0,
                has_warning=0,
                component_count=0,
                rare_event_count=0,
                rare_event_ratio=0.0,
                event_entropy=0.0,
                template_counts={},
            )

        template_counts: Dict[str, int] = {}
        error_count = 0
        warn_count = 0
        components: Set[str] = set()

        for ev in events:
            # Event template / ID
            tid = str(ev.get("EventId") or ev.get("event_id") or ev.get("template_id") or "UNKNOWN")
            template_counts[tid] = template_counts.get(tid, 0) + 1

            # Log level
            level = str(ev.get("Level") or ev.get("level") or "").upper()
            raw_msg = str(ev.get("Content") or ev.get("content") or ev.get("raw_message") or "")
            if level in ("ERROR", "FATAL", "CRITICAL") or "ERROR" in raw_msg:
                error_count += 1
            elif level in ("WARN", "WARNING") or "WARN" in raw_msg:
                warn_count += 1

            # Component
            comp = ev.get("Component") or ev.get("component")
            if comp:
                components.add(str(comp))

        # Rare events
        rare_count = sum(cnt for tid, cnt in template_counts.items() if tid in self.rare_templates)
        rare_ratio = (rare_count / total_events) if total_events > 0 else 0.0

        # Shannon Entropy of event templates
        entropy = 0.0
        for cnt in template_counts.values():
            p = cnt / total_events
            if p > 0:
                entropy -= p * math.log2(p)

        return BlockFeatures(
            block_id=block_id,
            total_events=total_events,
            unique_templates=len(template_counts),
            error_count=error_count,
            warn_count=warn_count,
            has_error=int(error_count > 0),
            has_warning=int(warn_count > 0),
            component_count=len(components),
            rare_event_count=rare_count,
            rare_event_ratio=rare_ratio,
            event_entropy=entropy,
            template_counts=template_counts,
        )

    def _build_feature_vector(self, bf: BlockFeatures) -> List[float]:
        """Convert a BlockFeatures object into a flat float vector using learned vocabulary."""
        vec = [
            float(bf.total_events),
            float(bf.unique_templates),
            float(bf.error_count),
            float(bf.warn_count),
            float(bf.has_error),
            float(bf.has_warning),
            float(bf.component_count),
            float(bf.rare_event_count),
            float(bf.rare_event_ratio),
            float(bf.event_entropy),
        ]
        # Append template frequency columns
        for tid in self.vocab_templates:
            vec.append(float(bf.template_counts.get(tid, 0)))

        return vec

    def _determine_feature_names(self) -> List[str]:
        names = [
            "total_events",
            "unique_templates",
            "error_count",
            "warn_count",
            "has_error",
            "has_warning",
            "component_count",
            "rare_event_count",
            "rare_event_ratio",
            "event_entropy",
        ]
        for tid in self.vocab_templates:
            names.append(f"template_{tid}")
        return names

    # ── Grouping Helpers ───────────────────────────────────────────────────

    @staticmethod
    def group_events_by_block(
        data: Union[pd.DataFrame, Sequence[Dict[str, Any]]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Groups raw or structured event records by BlockId."""
        groups: Dict[str, List[Dict[str, Any]]] = {}

        if isinstance(data, pd.DataFrame):
            records = data.to_dict(orient="records")
        else:
            records = data

        for row in records:
            # Check explicit BlockId column or block_id
            b_id = row.get("BlockId") or row.get("block_id")
            if not b_id:
                # Check block_ids list
                b_ids_list = row.get("block_ids")
                if b_ids_list and isinstance(b_ids_list, (list, tuple)) and len(b_ids_list) > 0:
                    b_id = b_ids_list[0]
            if not b_id:
                # Fallback to regex in Content or raw_message
                txt = str(row.get("Content") or row.get("content") or row.get("raw_message") or "")
                m = BLOCK_ID_REGEX.findall(txt)
                if m:
                    b_id = m[0]
            if not b_id:
                # Check explicit group_id (e.g. cluster_E1) or fallback to event_id / cluster_id
                b_id = row.get("group_id")
                if not b_id:
                    ev_id = row.get("EventId") or row.get("event_id") or row.get("template_id")
                    if ev_id and ev_id not in ("E0", "E_ERR"):
                        b_id = f"cluster_{ev_id}"

            if b_id:
                if b_id not in groups:
                    groups[b_id] = []
                groups[b_id].append(row)

        return groups

    # ── Fit and Transform ──────────────────────────────────────────────────

    def fit(self, block_dict: Dict[str, List[Dict[str, Any]]]) -> "BlockFeatureExtractor":
        """
        Fit vocabulary, rare template thresholds, and scaler on training blocks ONLY.
        """
        # Count overall template occurrences across training split
        overall_template_counts: Dict[str, int] = {}
        total_template_tokens = 0

        for events in block_dict.values():
            for ev in events:
                tid = str(ev.get("EventId") or ev.get("event_id") or ev.get("template_id") or "UNKNOWN")
                overall_template_counts[tid] = overall_template_counts.get(tid, 0) + 1
                total_template_tokens += 1

        # Select top templates for vocabulary
        sorted_templates = sorted(overall_template_counts.items(), key=lambda x: x[1], reverse=True)
        if self.max_templates:
            self.vocab_templates = [t for t, _ in sorted_templates[:self.max_templates]]
        else:
            self.vocab_templates = [t for t, _ in sorted_templates]

        # Identify rare templates (frequency < rare_threshold in training split)
        self.rare_templates = {
            t for t, cnt in overall_template_counts.items()
            if (cnt / max(total_template_tokens, 1)) < self.rare_threshold
        }

        self.feature_names_ = self._determine_feature_names()

        # Build training matrix to fit scaler
        raw_rows = []
        for block_id, events in block_dict.items():
            bf = self._extract_single_block_features(block_id, events)
            raw_rows.append(self._build_feature_vector(bf))

        if raw_rows:
            X_raw = np.array(raw_rows, dtype=np.float32)
            if self.scaler:
                self.scaler.fit(X_raw)

        self.is_fitted = True
        logger.info(
            "BlockFeatureExtractor fitted",
            n_blocks=len(block_dict),
            n_features=len(self.feature_names_),
            vocab_size=len(self.vocab_templates),
            rare_templates=len(self.rare_templates),
        )
        return self

    def transform(
        self,
        block_dict: Dict[str, List[Dict[str, Any]]],
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Transform blocks into numerical feature matrix using learned training parameters.
        Returns:
            (feature_matrix, block_ids_list)
        """
        if not self.is_fitted:
            raise RuntimeError("BlockFeatureExtractor must be fitted before calling transform().")

        block_ids = list(block_dict.keys())
        raw_rows = []
        for b_id in block_ids:
            events = block_dict[b_id]
            bf = self._extract_single_block_features(b_id, events)
            raw_rows.append(self._build_feature_vector(bf))

        if not raw_rows:
            return np.empty((0, len(self.feature_names_)), dtype=np.float32), []

        X_raw = np.array(raw_rows, dtype=np.float32)
        X = self.scaler.transform(X_raw) if self.scaler else X_raw
        return X, block_ids

    def fit_transform(
        self,
        block_dict: Dict[str, List[Dict[str, Any]]],
    ) -> Tuple[np.ndarray, List[str]]:
        """Fit on blocks and return transformed feature matrix."""
        self.fit(block_dict)
        return self.transform(block_dict)

    def fit_aggregated(
        self,
        template_token_counts: Dict[str, int],
        total_template_tokens: int,
        feature_batches: Iterable[Sequence[BlockFeatures]] | Callable[[], Iterable[Sequence[BlockFeatures]]],
    ) -> "BlockFeatureExtractor":
        """Fit vocabulary and scaler from compact block summaries.

        This is the bounded-memory training counterpart to :meth:`fit`; each
        batch contains one ``BlockFeatures`` summary per block, not raw events.
        """
        sorted_templates = sorted(template_token_counts.items(), key=lambda x: (-x[1], x[0]))
        self.vocab_templates = [
            t for t, _ in (sorted_templates[:self.max_templates] if self.max_templates else sorted_templates)
        ]
        self.rare_templates = {
            t for t, count in template_token_counts.items()
            if (count / max(total_template_tokens, 1)) < self.rare_threshold
        }
        self.feature_names_ = self._determine_feature_names()

        batches = feature_batches() if callable(feature_batches) else feature_batches
        seen = 0
        for batch in batches:
            if not batch:
                continue
            X_raw = np.asarray([self._build_feature_vector(bf) for bf in batch], dtype=np.float32)
            if self.scaler is not None:
                self.scaler.partial_fit(X_raw)
            seen += len(batch)
        if seen == 0:
            raise ValueError("Cannot fit BlockFeatureExtractor without training blocks.")
        self.is_fitted = True
        logger.info("BlockFeatureExtractor fitted from aggregates", n_blocks=seen, n_features=len(self.feature_names_))
        return self

    def transform_aggregated(
        self,
        block_features: Sequence[BlockFeatures],
    ) -> Tuple[np.ndarray, List[str]]:
        """Transform a bounded batch of already aggregated block features."""
        if not self.is_fitted:
            raise RuntimeError("BlockFeatureExtractor must be fitted before calling transform_aggregated().")
        block_ids = [bf.block_id for bf in block_features]
        if not block_features:
            return np.empty((0, len(self.feature_names_)), dtype=np.float32), []
        X_raw = np.asarray([self._build_feature_vector(bf) for bf in block_features], dtype=np.float32)
        X = self.scaler.transform(X_raw) if self.scaler is not None else X_raw
        return X, block_ids

    # ── Serialization ──────────────────────────────────────────────────────

    def save(self, filepath: str | Path) -> None:
        """Persist extractor state and scaler parameters to a JSON file."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        scaler_state = None
        if self.scaler is not None and hasattr(self.scaler, "mean_"):
            scaler_state = {
                "mean": self.scaler.mean_.tolist(),
                "var": self.scaler.var_.tolist(),
                "scale": self.scaler.scale_.tolist(),
            }

        state = {
            "rare_threshold": self.rare_threshold,
            "max_templates": self.max_templates,
            "scale_features": self.scale_features,
            "vocab_templates": self.vocab_templates,
            "rare_templates": list(self.rare_templates),
            "feature_names": self.feature_names_,
            "is_fitted": self.is_fitted,
            "scaler": scaler_state,
        }
        filepath.write_text(json.dumps(state, indent=2), encoding="utf-8")
        logger.info("Saved BlockFeatureExtractor state", path=str(filepath))

    @classmethod
    def load(cls, filepath: str | Path) -> "BlockFeatureExtractor":
        """Load extractor state from JSON file."""
        filepath = Path(filepath)
        state = json.loads(filepath.read_text(encoding="utf-8"))

        extractor = cls(
            rare_threshold=state["rare_threshold"],
            max_templates=state["max_templates"],
            scale_features=state["scale_features"],
        )
        extractor.vocab_templates = state["vocab_templates"]
        extractor.rare_templates = set(state["rare_templates"])
        extractor.feature_names_ = state["feature_names"]
        extractor.is_fitted = state["is_fitted"]

        if state.get("scaler") and extractor.scaler is not None:
            s_data = state["scaler"]
            extractor.scaler.mean_ = np.array(s_data["mean"], dtype=np.float64)
            extractor.scaler.var_ = np.array(s_data["var"], dtype=np.float64)
            extractor.scaler.scale_ = np.array(s_data["scale"], dtype=np.float64)
            extractor.scaler.n_features_in_ = len(s_data["mean"])

        logger.info("Loaded BlockFeatureExtractor", path=str(filepath))
        return extractor
