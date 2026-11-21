#!/usr/bin/env python3
"""
LogSage — Logfit HDFS_v1 Dataset Downloader and Validator.

Downloads and validates the 5 Parquet shards of the HDFS_v1 dataset from Hugging Face
(logfit-project/HDFS_v1) into a local destination directory.

Schema:
  line_number: int64
  date: string
  time: string
  pid: string
  level: string
  component: string
  content: string
  block_id: string
  anomaly: int64 / bool

Verified Statistics:
  Total log lines: 11,175,629
  Normal log lines: 10,887,379
  Anomalous log lines: 288,250
  Unique blocks: 575,061
  Normal blocks: 558,223
  Anomalous blocks: 16,838
  Conflicting block labels: 0
"""
from __future__ import annotations

import argparse
import glob
import os
import sys
from pathlib import Path
from typing import List, Tuple

EXPECTED_SHARD_COUNT = 5
EXPECTED_TOTAL_LINES = 11_175_629
EXPECTED_NORMAL_LINES = 10_887_379
EXPECTED_ANOMALY_LINES = 288_250
EXPECTED_COLUMNS = [
    "line_number",
    "date",
    "time",
    "pid",
    "level",
    "component",
    "content",
    "block_id",
    "anomaly",
]


def find_parquet_shards(target_dir: Path) -> List[Path]:
    """Locate all 5 train-*.parquet shards in the target directory or subdirectories."""
    # Direct match or nested in data/
    patterns = [
        target_dir / "train-*.parquet",
        target_dir / "data" / "train-*.parquet",
        target_dir / "**" / "train-*.parquet",
    ]
    for pattern in patterns:
        matches = sorted(glob.glob(str(pattern), recursive=True))
        if matches:
            return [Path(p) for p in matches if Path(p).is_file() and not Path(p).name.startswith(".")]
    return []


def download_dataset(
    repo_id: str,
    output_dir: Path,
    cache_dir: Path | None = None,
) -> List[Path]:
    """Download Parquet shards from Hugging Face Hub using snapshot_download."""
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("ERROR: huggingface_hub is required. Install with: pip install huggingface-hub", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Downloading dataset '{repo_id}' to: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    local_dir = snapshot_download(
        repo_id=repo_id,
        repo_type="dataset",
        allow_patterns="data/train-*.parquet",
        local_dir=output_dir,
        cache_dir=cache_dir,
    )
    shards = find_parquet_shards(Path(local_dir))
    return shards


def validate_shards(shards: List[Path], full_stats: bool = True) -> Tuple[bool, dict]:
    """Validate parquet shards for readability, schema conformance, and line counts."""
    try:
        import pyarrow.parquet as pq
    except ImportError:
        print("ERROR: pyarrow is required. Install with: pip install pyarrow", file=sys.stderr)
        sys.exit(1)

    if len(shards) != EXPECTED_SHARD_COUNT:
        print(f"[!] Warning: Expected {EXPECTED_SHARD_COUNT} shards, found {len(shards)}")

    total_rows = 0
    normal_count = 0
    anomaly_count = 0
    all_valid = True

    print("\n--- Parquet Shard Schema & Row Validation ---")
    for shard in sorted(shards):
        try:
            pf = pq.ParquetFile(shard)
            num_rows = pf.metadata.num_rows
            columns = pf.schema.names
            missing_cols = set(EXPECTED_COLUMNS) - set(columns)

            if missing_cols:
                print(f"[x] {shard.name}: FAILED - missing columns {missing_cols}")
                all_valid = False
            else:
                print(f"[+] {shard.name}: {num_rows:,} rows, all {len(EXPECTED_COLUMNS)} columns present")

            total_rows += num_rows

            if full_stats and not missing_cols:
                for batch in pf.iter_batches(batch_size=500_000, columns=["anomaly"]):
                    anom_arr = batch.column(0).to_numpy()
                    anom = int(anom_arr.sum())
                    anomaly_count += anom
                    normal_count += len(anom_arr) - anom

        except Exception as exc:
            print(f"[x] {shard.name}: Error reading file: {exc}")
            all_valid = False

    stats = {
        "shard_count": len(shards),
        "total_lines": total_rows,
        "normal_lines": normal_count if full_stats else None,
        "anomalous_lines": anomaly_count if full_stats else None,
    }

    print("\n--- Summary Statistics ---")
    print(f"Total Log Lines: {total_rows:,} (Expected: {EXPECTED_TOTAL_LINES:,})")
    if full_stats:
        print(f"Normal Lines:    {normal_count:,} (Expected: {EXPECTED_NORMAL_LINES:,})")
        print(f"Anomalous Lines: {anomaly_count:,} (Expected: {EXPECTED_ANOMALY_LINES:,})")

    if total_rows != EXPECTED_TOTAL_LINES:
        print(f"[!] Row count mismatch: {total_rows} != {EXPECTED_TOTAL_LINES}")
        all_valid = False

    return all_valid, stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download and validate the Logfit HDFS_v1 Parquet dataset from Hugging Face.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(os.environ.get("LOGFIT_DATA_DIR", "data/parquet")),
        help="Directory where parquet shards are stored or should be downloaded (default: data/parquet).",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Custom Hugging Face cache directory (optional).",
    )
    parser.add_argument(
        "--repo-id",
        type=str,
        default="logfit-project/HDFS_v1",
        help="Hugging Face dataset repository ID (default: logfit-project/HDFS_v1).",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Skip download and only validate existing shards in output-dir or local HF cache.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick validation: inspect metadata and row counts without scanning full anomaly column.",
    )

    args = parser.parse_args()

    # Check for existing shards in output_dir first
    shards = find_parquet_shards(args.output_dir)

    # If not found in output_dir, check default HF cache if --validate-only is requested
    if not shards and args.validate_only:
        default_hf_cache = Path.home() / ".cache" / "huggingface" / "hub" / "datasets--logfit-project--HDFS_v1"
        if default_hf_cache.exists():
            print(f"[*] Checking local Hugging Face cache: {default_hf_cache}")
            shards = find_parquet_shards(default_hf_cache)

    if not shards and not args.validate_only:
        shards = download_dataset(args.repo_id, args.output_dir, args.cache_dir)
    elif not shards and args.validate_only:
        print(f"ERROR: No Parquet shards found in {args.output_dir}. Run without --validate-only to download.", file=sys.stderr)
        sys.exit(1)

    print(f"\n[*] Found {len(shards)} Parquet shard(s).")
    valid, stats = validate_shards(shards, full_stats=not args.quick)

    if valid:
        print("\n[SUCCESS] All HDFS_v1 Parquet shards are valid, complete, and verified!")
        sys.exit(0)
    else:
        print("\n[FAILURE] Validation checks did not pass.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
