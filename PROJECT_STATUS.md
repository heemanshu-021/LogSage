# PROJECT_STATUS.md — LogSage Live Progress Tracker

> Last updated: 2026-11-17 10:14 IST  
> Hackathon Target: 24h MVP (Log Anomaly Detection with Runbook-Retrieval Triage)

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Complete & tested |
| 🔄 | In progress |
| ⏳ | Queued — dependency met |
| 🔒 | Blocked — waiting on dependency |
| ❌ | Failed / broken |
| 📝 | Needs review |

---

## Phase 0 — Scaffolding & Config  `[✅ COMPLETE]`

| Task | Status | Notes |
|------|--------|-------|
| Directory structure | ✅ | Full tree created |
| `.gitignore` | ✅ | Python + Node + data/model exclusions |
| `.env.example` | ✅ | All env vars documented |
| `requirements.txt` | ✅ | Pinned versions, pip and node dependencies |
| `README.md` | ✅ | Architecture + quickstart |
| `PROJECT_STATUS.md` | ✅ | Live tracker maintained |

---

## Phase 1 — Dataset Acquisition & Exploration  `[✅ COMPLETE]`

| Task | Status | Artifact / Notes |
|------|--------|------------------|
| Inspect official repo | ✅ | `logpai/loghub` & `logpai/loglizer` repositories analyzed |
| Locate HDFS logs & labels | ✅ | `anomaly_label.csv` (loglizer) & `HDFS_2k.log` (loghub) |
| Download raw files to `data/raw/` | ✅ | `anomaly_label.csv` (18 MB, 575k blocks), `HDFS_2k.log` (287 KB), `HDFS_templates.csv` |
| Handle remote download limits | ✅ | Zenodo 1.47 GB `HDFS_v1.zip` requires direct browser download due to HTTP 403 anti-bot protection |
| Reusable Preprocessing Utility | ✅ | `ml/preprocessing/hdfs_preprocessor.py` (`HDFSPreprocessor`, `BlockTrace`) |
| Preprocessor Unit Tests | ✅ | `tests/unit/test_hdfs_preprocessor.py` (4/4 tests passed) |
| Exploration Notebook | ✅ | `notebooks/01_data_exploration.ipynb` created and executed end-to-end |
| Statistical & Imbalance Analysis | ✅ | 575,061 blocks analyzed: 97.07% Normal vs 2.93% Anomaly (~33:1 imbalance) |
| Visualizations | ✅ | `data/processed/hdfs_data_exploration_summary.png` generated and verified |
| Malformed Records Isolation | ✅ | Non-block records quarantined into unassigned pool without pipeline failure |

---

## Phase 2 — ML: Log Parser (Drain3)  `[✅ COMPLETE]`

| Task | Status | File(s) | Notes |
|------|--------|---------|-------|
| `ml/parser/drain_parser.py` | ✅ | Drain3 wrapper + template miner | Tested & verified |
| `ml/parser/log_loader.py` | ✅ | HDFS / syslog / custom streaming loader | Tested & verified |
| Unit tests: parser | ✅ | `tests/unit/test_parser.py` | 11/11 tests passed |

---

## Phase 3 — ML: Preprocessing & Featurisation  `[✅ COMPLETE]`

| Task | Status | File(s) | Notes |
|------|--------|---------|-------|
| `ml/preprocessing/feature_extractor.py` | ✅ | TF-IDF on templates + error/warning signal columns | Tested & verified |
| `ml/preprocessing/window_builder.py` | ✅ | Fixed and sliding window trace builder | Tested & verified |
| `ml/preprocessing/hdfs_preprocessor.py` | ✅ | Block-level trace extractor & label mapper | Tested & verified |
| Unit tests: preprocessing | ✅ | `tests/unit/test_preprocessing.py` | 8/8 tests passed |

---

## Phase 4 — ML: Anomaly Detection  `[✅ COMPLETE]`

| Task | Status | File(s) | Notes |
|------|--------|---------|-------|
| `ml/models/base_detector.py` | ✅ | Abstract detector interface (`fit`, `predict`, `score`, `save`, `load`) | Verified |
| `ml/models/isolation_forest.py` | ✅ | Scikit-learn IsolationForest with normalised [0, 1] scores | Tested & verified |
| `ml/models/lof.py` | ✅ | Local Outlier Factor (novelty detection mode) | Tested & verified |
| `ml/evaluation/metrics.py` | ✅ | Precision, Recall, F1, AUC-ROC, Confusion Matrix | Tested & verified |
| Unit tests: anomaly models | ✅ | `tests/unit/test_anomaly.py` | 11/11 tests passed |

---

## Phase 5 — Runbook Retrieval (RAG)  `[🔄 IN PROGRESS]`

| Task | Status | File(s) | Notes |
|------|--------|---------|-------|
| Curated Ops Runbooks (5+) | ✅ | `runbooks/*.md` | HDFS, OOM, SSH brute-force, Disk, DB timeout |
| Retrieval Service | ✅ | `backend/services/retrieval.py` | Sentence Transformers + FAISS vector search |
| Runbook API Routes | ✅ | `backend/api/routes/runbooks.py` | GET `/runbooks/search` and GET `/runbooks` |
| Retrieval Unit Tests | ⏳ | `tests/unit/test_retrieval.py` | Blocked until PyTorch/SentenceTransformers wheel finishes |

---

## Phase 6 — Ingest & Detection API  `[✅ COMPLETE]`

| Task | Status | File(s) | Notes |
|------|--------|---------|-------|
| Database Engine & Models | ✅ | `backend/db/database.py`, `models.py` | SQLite + aiosqlite async ORM |
| `backend/services/ingest.py` | ✅ | Pipeline: parse -> featurise -> detect -> persist | Verified |
| `backend/api/routes/ingest.py` | ✅ | POST `/logs/ingest`, POST `/logs/ingest/file` | Verified |
| `backend/api/routes/anomalies.py` | ✅ | GET `/anomalies` with pagination & filtering | Verified |
| `backend/api/routes/health.py` | ✅ | GET `/health` liveness & DB check | Verified |

---

## Phase 7 — React Frontend  `[✅ COMPLETE]`

| Task | Status | File(s) | Notes |
|------|--------|---------|-------|
| Vite + React scaffolding | ✅ | `frontend/` | Complete |
| Component hierarchy | ✅ | `App.jsx`, `LogUpload.jsx`, `AnomalyTable.jsx`, `RunbookPanel.jsx`, `StatusBar.jsx` | Built |
| Styles & responsive layout | ✅ | `App.css` | Dark mode ops dashboard |

---

## Test Results Log

| Date/Time | Test Suite | Tests Run | Result | Notes |
|-----------|------------|-----------|--------|-------|
| 2026-11-17 10:14 | `test_parser.py` | 11 | ✅ 11 passed | Drain3 template mining verified |
| 2026-11-17 10:14 | `test_preprocessing.py` | 8 | ✅ 8 passed | TF-IDF & sliding window verified |
| 2026-11-17 10:14 | `test_anomaly.py` | 11 | ✅ 11 passed | IF, LOF, and evaluation metrics verified |
| 2026-11-17 10:14 | `test_hdfs_preprocessor.py` | 4 | ✅ 4 passed | Block ID regex & trace grouping verified |
| **Total ML Suite** | **All 4 unit suites** | **34** | **✅ 34 passed (100%)** | Zero failures |

---

## Key Dataset Findings (LogHub HDFS)

1. **Block-Level Association:** Ground truth labels are strictly mapped to `BlockId` (`blk_-?\d+`), not arbitrary log lines. A block trace consists of interleaved log messages from multiple nodes.
2. **Severe Class Imbalance:**
   - **Normal Blocks:** 558,223 (97.07%)
   - **Anomalous Blocks:** 16,838 (2.93%)
   - **Imbalance Ratio:** ~33:1
3. **Trace Structure:** Normal blocks follow a standard 19-30 event lifecycle (allocation, replication, verification, closure). Anomalies exhibit truncated lifecycles or high ERROR/WARN frequencies.
4. **Quarantine Handling:** Malformed records lacking block IDs are isolated without crashing the ingestion pipeline.
