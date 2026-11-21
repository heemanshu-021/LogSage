# Logfit HDFS_v1 Dataset Documentation & Teammate Setup Guide

## 1. Overview & Dataset Selection

For production log anomaly detection, LogSage uses the **Logfit HDFS_v1** benchmark dataset:
- **Hugging Face Repository**: [`logfit-project/HDFS_v1`](https://huggingface.co/datasets/logfit-project/HDFS_v1)
- **Format**: 5 Parquet shards (`train-00000-of-00005.parquet` through `train-00004-of-00005.parquet`)
- **Total Size**: ~434.8 MB (414.6 MiB) for the five Parquet files (Hugging Face metadata checked 2026-11-21)
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
> The Logfit HDFS_v1 shards and line-level labels were downloaded and validated on 2026-11-21. Full block-level model training is now complete; measured results and split details are below.

### ML Phase 1: completed training and evaluation

Training command:

```bash
python ml/train_and_evaluate.py --dataset logfit
```

The pipeline reads Parquet record batches, parses content with Drain3, and aggregates event counts, template frequencies, error/warning counts, and component diversity into an ignored local SQLite staging database. The split is deterministic by `block_id` using SHA-256 and random seed 42: 70% training, 10% validation, and 20% held-out test. The feature vocabulary, rare-template set, and scaler are fit only on training blocks. Validation labels select the prediction cutoff by F1; test labels are not used for selection.

The Isolation Forest is fit on the mixed-label training feature matrix. Labels are used for the training contamination prior, validation cutoff selection, and evaluation; they are never included as input features. This preserves the existing unsupervised detector and feature architecture.

Verified block totals: 575,061 blocks (558,223 normal and 16,838 anomalous), with zero conflicting labels. The held-out test set contains 114,803 blocks (3,362 anomalous). Results:

| Metric | Held-out test |
|---|---:|
| Precision | 0.7622 |
| Recall | 0.8659 |
| F1 | 0.8108 |
| Specificity | 0.9919 |
| Accuracy | 0.9882 |
| ROC-AUC | 0.9942 |
| PR-AUC | 0.7927 |
| TP / FP / FN / TN | 2,911 / 908 / 451 / 110,533 |

The full machine-readable report is at `data/processed/logfit_training_report.json`. The model, feature extractor, and Drain3 JSON/native binary snapshot are saved at `ml/models/saved/`; these large/local artifacts remain excluded from Git. `PipelineService` loads the trained parser state and model artifacts on startup, and `/api/logs/analyze` was exercised with real held-out anomalous block lines, creating an incident with ML readiness enabled.

The former per-line TF-IDF ingest service was retired because it trained on live requests and did not use the trained block-level artifacts. The mounted application uses `PipelineService` and the trained block-level artifacts.
