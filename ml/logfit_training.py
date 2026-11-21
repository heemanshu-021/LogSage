"""Memory-conscious, block-isolated training on Logfit HDFS_v1 Parquet shards."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import platform
import sqlite3
import time
from collections import defaultdict
from pathlib import Path
from typing import Iterator, Sequence

import numpy as np
import pyarrow.parquet as pq
from sklearn.metrics import precision_recall_curve

from backend.core.config import settings
from ml.evaluation.evaluate import evaluate_predictions, generate_evaluation_plots
from ml.models.isolation_forest import IsolationForestDetector
from ml.parser.drain_parser import DrainParser
from ml.preprocessing.feature_extraction import BlockFeatureExtractor, BlockFeatures

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "parquet"
DEFAULT_ARTIFACT_DIR = Path(settings.MODEL_SAVE_DIR)
REPORT_PATH = ROOT / "data" / "processed" / "logfit_training_report.json"
PLOT_PATH = ROOT / "data" / "processed" / "logfit_evaluation.png"
PARSE_COLUMNS = ["line_number", "level", "component", "content", "block_id", "anomaly"]


def _split(block_id: str, seed: int = 42) -> str:
    """Deterministic block-level 70/10/20 split, independent of row order."""
    bucket = int.from_bytes(hashlib.sha256(f"{seed}:{block_id}".encode()).digest()[:4], "big") % 100
    return "train" if bucket < 70 else ("validation" if bucket < 80 else "test")


def _create_store(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    conn.executescript("""
        PRAGMA journal_mode=WAL;
        PRAGMA synchronous=NORMAL;
        PRAGMA temp_store=MEMORY;
        CREATE TABLE blocks (
            block_id TEXT PRIMARY KEY, label INTEGER NOT NULL, split TEXT NOT NULL,
            total_events INTEGER NOT NULL DEFAULT 0, error_count INTEGER NOT NULL DEFAULT 0,
            warn_count INTEGER NOT NULL DEFAULT 0, component_count INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE templates (
            block_id TEXT NOT NULL, template_id TEXT NOT NULL, count INTEGER NOT NULL,
            PRIMARY KEY (block_id, template_id)
        );
        CREATE TABLE components (
            block_id TEXT NOT NULL, component TEXT NOT NULL, PRIMARY KEY (block_id, component)
        );
        CREATE TABLE label_seen (block_id TEXT NOT NULL, label INTEGER NOT NULL,
            PRIMARY KEY (block_id, label));
        CREATE INDEX idx_blocks_split ON blocks(split, block_id);
        CREATE INDEX idx_templates_template ON templates(template_id);
    """)
    return conn


def _flush_batch(conn: sqlite3.Connection, local: dict) -> None:
    if not local:
        return
    conn.executemany(
        "INSERT INTO blocks(block_id,label,split,total_events,error_count,warn_count) VALUES(?,?,?,?,?,?) "
        "ON CONFLICT(block_id) DO UPDATE SET total_events=total_events+excluded.total_events, "
        "error_count=error_count+excluded.error_count, warn_count=warn_count+excluded.warn_count",
        (
            (bid, v["label"], v["split"], v["total"], v["errors"], v["warns"])
            for bid, v in local.items()
        ),
    )
    conn.executemany(
        "INSERT OR IGNORE INTO label_seen VALUES(?,?)",
        ((bid, v["label"]) for bid, v in local.items()),
    )
    conn.executemany(
        "INSERT OR IGNORE INTO label_seen VALUES(?,?)",
        ((bid, label) for bid, v in local.items() for label in v["conflicts"]),
    )
    conn.executemany(
        "INSERT OR IGNORE INTO components VALUES(?,?)",
        ((bid, comp) for bid, v in local.items() for comp in v["components"]),
    )
    conn.executemany(
        "INSERT INTO templates(block_id,template_id,count) VALUES(?,?,?) "
        "ON CONFLICT(block_id,template_id) DO UPDATE SET count=count+excluded.count",
        ((bid, tid, count) for bid, v in local.items() for tid, count in v["templates"].items()),
    )
    conn.commit()


def aggregate_dataset(
    shards: Sequence[Path], store_path: Path, batch_size: int = 50_000, max_rows: int | None = None
) -> tuple[sqlite3.Connection, DrainParser, dict]:
    """Parse all rows in bounded batches and aggregate per block in SQLite."""
    conn = _create_store(store_path)
    parser = DrainParser(config_path=ROOT / "ml" / "parser" / "parser_config.ini")
    rows_seen = 0
    started = time.time()
    for shard in shards:
        parquet = pq.ParquetFile(shard)
        for batch in parquet.iter_batches(
            batch_size=batch_size, columns=PARSE_COLUMNS, use_threads=True
        ):
            local: dict = {}
            for row in batch.to_pylist():
                block_id = str(row.get("block_id") or "").strip()
                if not block_id:
                    continue
                label = int(row.get("anomaly") or 0)
                split = _split(block_id)
                entry = local.get(block_id)
                if entry is None:
                    entry = {
                        "label": label,
                        "split": split,
                        "total": 0,
                        "errors": 0,
                        "warns": 0,
                        "components": set(),
                        "templates": defaultdict(int),
                        "conflicts": set(),
                    }
                    local[block_id] = entry
                elif entry["label"] != label:
                    entry["conflicts"].add(label)

                message = str(row.get("content") or "")
                template_id, _template = parser.parse_template(
                    message, update_model=(split == "train")
                )
                template_id = str(template_id or "UNKNOWN")
                entry["templates"][template_id] += 1
                entry["total"] += 1
                level = str(row.get("level") or "").upper()
                if level in ("ERROR", "FATAL", "CRITICAL") or "ERROR" in message:
                    entry["errors"] += 1
                elif level in ("WARN", "WARNING") or "WARN" in message:
                    entry["warns"] += 1
                component = row.get("component")
                if component:
                    entry["components"].add(str(component))
                rows_seen += 1
                if max_rows is not None and rows_seen >= max_rows:
                    break
            _flush_batch(conn, local)
            if rows_seen and rows_seen % (batch_size * 10) < batch_size:
                print(f"Parsed {rows_seen:,} rows ({time.time() - started:.1f}s)", flush=True)
            if max_rows is not None and rows_seen >= max_rows:
                break
        if max_rows is not None and rows_seen >= max_rows:
            break
    conn.execute(
        "UPDATE blocks SET component_count=(SELECT COUNT(*) FROM components c WHERE c.block_id=blocks.block_id)"
    )
    conn.commit()
    counts = {
        "rows": rows_seen,
        "blocks": conn.execute("SELECT COUNT(*) FROM blocks").fetchone()[0],
        "labels": {
            int(label): int(n)
            for label, n in conn.execute("SELECT label,COUNT(*) FROM blocks GROUP BY label")
        },
        "splits": {
            split: int(n)
            for split, n in conn.execute("SELECT split,COUNT(*) FROM blocks GROUP BY split")
        },
        "conflicting_blocks": conn.execute(
            "SELECT COUNT(*) FROM (SELECT block_id FROM label_seen GROUP BY block_id HAVING COUNT(*)>1)"
        ).fetchone()[0],
        "elapsed_seconds": round(time.time() - started, 2),
    }
    return conn, parser, counts


def _iter_summaries(
    conn: sqlite3.Connection,
    split: str,
    rare_templates: set[str] | None = None,
    batch_size: int = 500,
) -> Iterator[list[BlockFeatures]]:
    rare = rare_templates or set()
    cursor = conn.execute(
        "SELECT block_id,label,total_events,error_count,warn_count,component_count FROM blocks "
        "WHERE split=? ORDER BY block_id",
        (split,),
    )
    while rows := cursor.fetchmany(batch_size):
        ids = [row[0] for row in rows]
        placeholders = ",".join("?" for _ in ids)
        template_map: dict[str, dict[str, int]] = defaultdict(dict)
        for bid, tid, count in conn.execute(
            f"SELECT block_id,template_id,count FROM templates WHERE block_id IN ({placeholders})",
            ids,
        ):
            template_map[bid][tid] = int(count)
        features: list[BlockFeatures] = []
        for bid, _label, total, errors, warns, components in rows:
            counts = template_map.get(bid, {})
            entropy = -sum(
                (n / total) * math.log2(n / total) for n in counts.values() if n and total
            )
            rare_count = sum(n for tid, n in counts.items() if tid in rare)
            features.append(
                BlockFeatures(
                    block_id=bid,
                    total_events=total,
                    unique_templates=len(counts),
                    error_count=errors,
                    warn_count=warns,
                    has_error=int(errors > 0),
                    has_warning=int(warns > 0),
                    component_count=components,
                    rare_event_count=rare_count,
                    rare_event_ratio=rare_count / total if total else 0.0,
                    event_entropy=entropy,
                    template_counts=counts,
                )
            )
        yield features


def _labels_for_batch(conn: sqlite3.Connection, block_ids: Sequence[str]) -> np.ndarray:
    if not block_ids:
        return np.empty((0,), dtype=np.int8)
    placeholders = ",".join("?" for _ in block_ids)
    by_id = {
        bid: label
        for bid, label in conn.execute(
            f"SELECT block_id,label FROM blocks WHERE block_id IN ({placeholders})", list(block_ids)
        )
    }
    return np.asarray([by_id[bid] for bid in block_ids], dtype=np.int8)


def _matrix_for_split(conn: sqlite3.Connection, extractor: BlockFeatureExtractor, split: str):
    xs, ys, ids = [], [], []
    for features in _iter_summaries(conn, split, extractor.rare_templates):
        X, batch_ids = extractor.transform_aggregated(features)
        xs.append(X)
        ys.append(_labels_for_batch(conn, batch_ids))
        ids.extend(batch_ids)
    if not xs:
        return (
            np.empty((0, len(extractor.feature_names_)), dtype=np.float32),
            np.empty((0,), dtype=np.int8),
            ids,
        )
    return np.concatenate(xs), np.concatenate(ys), ids


def _best_f1_threshold(y_true: np.ndarray, scores: np.ndarray) -> tuple[float, float]:
    precision, recall, thresholds = precision_recall_curve(y_true, scores)
    if thresholds.size == 0:
        return 0.5, 0.0
    f1 = 2 * precision[:-1] * recall[:-1] / np.maximum(precision[:-1] + recall[:-1], 1e-12)
    idx = int(np.argmax(f1))
    return float(thresholds[idx]), float(f1[idx])


def train_logfit(
    data_dir: Path = DATA_DIR,
    artifact_dir: Path = DEFAULT_ARTIFACT_DIR,
    max_rows: int | None = None,
    batch_size: int = 50_000,
) -> dict:
    shards = sorted(data_dir.rglob("train-*.parquet"))
    if len(shards) != 5:
        raise FileNotFoundError(
            f"Expected five Logfit Parquet shards under {data_dir}; found {len(shards)}"
        )
    store_path = (
        ROOT
        / "data"
        / "processed"
        / ("logfit_training_smoke.sqlite" if max_rows else "logfit_training.sqlite")
    )
    conn, parser, data_stats = aggregate_dataset(
        shards, store_path, batch_size=batch_size, max_rows=max_rows
    )
    if data_stats["conflicting_blocks"]:
        raise ValueError(f"Found {data_stats['conflicting_blocks']} blocks with conflicting labels")
    if set(data_stats["splits"]) != {"train", "validation", "test"}:
        raise ValueError("All three block splits must contain data")

    token_counts = {
        tid: int(count)
        for tid, count in conn.execute(
            "SELECT t.template_id,SUM(t.count) FROM templates t JOIN blocks b USING(block_id) "
            "WHERE b.split='train' GROUP BY t.template_id"
        )
    }
    total_tokens = sum(token_counts.values())
    extractor = BlockFeatureExtractor(rare_threshold=0.01, max_templates=50, scale_features=True)
    extractor.fit_aggregated(
        token_counts, total_tokens, lambda: _iter_summaries(conn, "train", extractor.rare_templates)
    )

    X_train, y_train, _ = _matrix_for_split(conn, extractor, "train")
    X_val, y_val, _ = _matrix_for_split(conn, extractor, "validation")
    X_test, y_test, test_ids = _matrix_for_split(conn, extractor, "test")
    if min(len(X_train), len(X_val), len(X_test)) == 0:
        raise ValueError("A split is empty; increase dataset size or remove --max-rows")

    contamination = float(np.mean(y_train))
    if not 0.0 < contamination < 0.5:
        raise ValueError(f"Training contamination {contamination:.5f} is outside (0, 0.5)")
    detector = IsolationForestDetector(
        n_estimators=150, contamination=contamination, random_state=42
    )
    detector.fit(X_train)

    # Select a decision threshold on validation only; the test split stays untouched.
    val_scores = detector.score(X_val)
    val_threshold, val_best_f1 = _best_f1_threshold(y_val, val_scores)
    val_preds = detector.predict(X_val, threshold=val_threshold)
    # Translate the normalized validation threshold to sklearn's persisted offset
    # so the backend's existing predict(X, threshold=None) uses the selected cutoff.
    raw_cutoff = detector.score_min_ + val_threshold * (detector.score_max_ - detector.score_min_)
    old_offset = float(detector.model.offset_)
    selected_offset = old_offset - raw_cutoff
    detector.model.offset_ = selected_offset
    detector.contamination = float(np.mean(val_preds))
    detector.model.contamination = detector.contamination
    train_raw = -detector.model.decision_function(X_train)
    detector.score_min_ = float(train_raw.min())
    detector.score_max_ = (
        float(train_raw.max()) if train_raw.max() > train_raw.min() else float(train_raw.min() + 1)
    )

    test_scores = detector.score(X_test)
    test_preds = detector.predict(X_test)
    report = evaluate_predictions(y_test, test_preds, test_scores)
    report.print_summary()
    native_val_report = evaluate_predictions(y_val, detector.predict(X_val), val_scores)
    plot_path = (
        PLOT_PATH if not max_rows else ROOT / "data" / "processed" / "logfit_smoke_evaluation.png"
    )
    generate_evaluation_plots(
        y_test, test_preds, test_scores, plot_path, title_suffix="Logfit HDFS_v1, held-out blocks"
    )

    artifact_dir.mkdir(parents=True, exist_ok=True)
    detector_path = artifact_dir / "isolation_forest.joblib"
    extractor_path = artifact_dir / "feature_extractor.json"
    detector.save(detector_path)
    extractor.save(extractor_path)
    parser_snapshot = artifact_dir / "drain_state.json"
    parser.save(parser_snapshot)

    reloaded_detector = IsolationForestDetector.load(detector_path)
    reloaded_extractor = BlockFeatureExtractor.load(extractor_path)
    X_test_reloaded, _, reloaded_ids = _matrix_for_split(conn, reloaded_extractor, "test")
    features_equal = bool(
        reloaded_ids == test_ids and np.allclose(X_test_reloaded, X_test, rtol=1e-6, atol=1e-6)
    )
    inference_equal = features_equal and bool(
        np.array_equal(reloaded_detector.predict(X_test_reloaded), test_preds)
    )
    del X_test_reloaded
    if not features_equal:
        raise RuntimeError("Reloaded feature extractor differs from the trained extractor")
    if not inference_equal:
        raise RuntimeError("Reloaded model predictions differ from the trained model")

    metrics = {
        "dataset": "logfit-project/HDFS_v1",
        "dataset_sha": "da85a01a6bd4218af49d6122e9add31880f2403a",
        "split_method": "sha256(seed:block_id) modulo 100; 70/10/20 train/validation/test",
        "seed": 42,
        "training_mode": "mixed-label unsupervised Isolation Forest; labels used for contamination, validation cutoff, and evaluation only",
        "runtime_versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scikit_learn": importlib.metadata.version("scikit-learn"),
            "pyarrow": importlib.metadata.version("pyarrow"),
            "drain3": importlib.metadata.version("drain3"),
        },
        "data": data_stats,
        "feature_count": len(extractor.feature_names_),
        "template_vocabulary_size": len(extractor.vocab_templates),
        "train_contamination_prior": contamination,
        "validation_selected_threshold": val_threshold,
        "validation_best_f1": val_best_f1,
        "validation_selected_cutoff_metrics": native_val_report.to_dict(),
        "test_metrics": report.to_dict(),
        "artifacts": {
            "detector": str(detector_path.relative_to(ROOT)),
            "extractor": str(extractor_path.relative_to(ROOT)),
            "drain_parser": str(parser_snapshot.relative_to(ROOT)),
            "drain_parser_binary": str(parser_snapshot.with_suffix(".bin").relative_to(ROOT)),
            "evaluation_plot": str(plot_path.relative_to(ROOT)),
        },
        "reloaded_test_predictions_equal": inference_equal,
        "reloaded_features_equal": features_equal,
        "max_rows_smoke_run": max_rows,
    }
    report_path = (
        REPORT_PATH if not max_rows else ROOT / "data" / "processed" / "logfit_smoke_report.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Saved report: {report_path}")
    print(f"Saved model artifacts: {artifact_dir}")
    conn.close()
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--batch-size", type=int, default=50_000)
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Smoke run only; writes separate smoke artifacts.",
    )
    args = parser.parse_args()
    artifact_dir = (
        args.artifact_dir
        if args.max_rows is None
        else ROOT / "data" / "processed" / "logfit_smoke_artifacts"
    )
    train_logfit(args.data_dir, artifact_dir, args.max_rows, args.batch_size)


if __name__ == "__main__":
    main()
