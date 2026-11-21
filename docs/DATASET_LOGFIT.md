# Logfit HDFS_v1 Dataset Documentation & Teammate Setup Guide

## 1. Overview & Dataset Selection

For production log anomaly detection, LogSage uses the **Logfit HDFS_v1** benchmark dataset:
- **Hugging Face Repository**: [`logfit-project/HDFS_v1`](https://huggingface.co/datasets/logfit-project/HDFS_v1)
- **Format**: 5 Parquet shards (`train-00000-of-00005.parquet` through `train-00004-of-00005.parquet`)
- **Total Size**: ~1.3 GB compressed
- **Git Status**: External dataset — strictly excluded from Git tracking via `.gitignore`.

## 2. Schema Specification

Each record in the dataset represents a single parsed log line with ground-truth block attribution and anomaly annotation:

| Column | Type | Description | Example |
|---|---|---|---|
| `line_number` | `int64` | 1-based log line sequence number | `1024` |
| `date` | `string` | Date string (YYMMDD) | `"081109"` |
| `time` | `string` | Time string (HHMMSS) | `"203518"` |
| `pid` | `string` | Process ID or thread ID | `"35"` |
| `level` | `string` | Log level | `"INFO"`, `"WARN"`, `"ERROR"` |
| `component` | `string` | Reporting Hadoop subsystem | `"dfs.DataNode$DataXceiver"` |
| `content` | `string` | Raw log line message content | `"Receiving block blk_-1608999687919862906 ..."` |
| `block_id` | `string` | HDFS block identifier | `"blk_-1608999687919862906"` |
| `anomaly` | `int64` | Ground-truth anomaly label (`0` = Normal, `1` = Anomaly) | `0` or `1` |

## 3. Verified Dataset Statistics

These statistics have been independently verified across the 5 Parquet shards:

- **Total Log Lines**: `11,175,629`
  - Shard 0: `2,235,126` lines
  - Shard 1: `2,235,126` lines
  - Shard 2: `2,235,126` lines
  - Shard 3: `2,235,126` lines
  - Shard 4: `2,235,125` lines
- **Normal Log Lines (`anomaly=0`)**: `10,887,379` (97.42%)
- **Anomalous Log Lines (`anomaly=1`)**: `288,250` (2.58%)
- **Unique HDFS Blocks**: `575,061`
  - Normal Blocks: `558,223` (97.07%)
  - Anomalous Blocks: `16,838` (2.93%)
  - Conflicting Block Labels: `0` (clean block-level separation)

## 4. Teammate Setup & Reproduction Instructions

Every teammate can reproduce the exact dataset locally using the automated script:

```bash
# 1. Ensure required dependencies are installed
pip install -r requirements.txt

# 2. Download and validate the dataset to data/parquet/
python scripts/download_logfit_dataset.py

# 3. Or specify a custom output directory via flag or environment variable
python scripts/download_logfit_dataset.py --output-dir /path/to/custom/data

# 4. If already downloaded, validate shards without re-downloading
python scripts/download_logfit_dataset.py --validate-only
```

## 5. Machine Learning Phase 1 Status & Remaining Work

> [!IMPORTANT]
> The Logfit HDFS_v1 dataset has been selected, schema-validated, and verified locally.
> **Full model training has NOT yet been completed.** Teammates will take over ML Phase 1 from here.

### Pending ML Tasks:
1. **Streaming Feature Extraction**:
   - Process Parquet shards in memory-efficient batches (never load 11.17M rows into a single in-memory dict).
   - Use `DrainParser` (with native `.bin` checkpoint persistence) to mine event templates.
   - Aggregate log lines by `block_id` into `BlockFeatureExtractor` vectors.
2. **Train/Test Block Split**:
   - Split by unique `block_id` (e.g. 80/20 train/test stratified by block label) BEFORE fitting scalers or rare-event thresholds to prevent data leakage.
3. **Model Training & Persistence**:
   - Train `IsolationForestDetector` (and optionally compare with `LOFDetector`).
   - Save artifacts to the exact paths expected by `PipelineService`:
     - `ml/models/saved/isolation_forest.joblib`
     - `ml/models/saved/feature_extractor.json`
4. **Comprehensive Evaluation**:
   - Evaluate on held-out test blocks using: Precision, Recall, F1-score, PR-AUC, and Confusion Matrix.
   - Verify that `PipelineService` automatically loads the saved model on startup and degrades gracefully to heuristic fallback if missing.
