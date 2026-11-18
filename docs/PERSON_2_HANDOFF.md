# LogSage — Person 2 Engineering Handoff Documentation

> **Document Version:** 1.0.0  
> **Date:** 2026-11-18  
> **Author:** Person 1 Audit & Stabilization Lead  
> **Target Audience:** Person 2 (Frontend, Integration, and Next-Phase Engineering)  
> **Project Repository:** LogSage (Log Anomaly Detection with Runbook-Retrieval Triage)  

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Completed Modules](#2-completed-modules)
3. [Repository Architecture](#3-repository-architecture)
4. [Exact Environment Setup Commands](#4-exact-environment-setup-commands)
5. [Exact Startup Commands](#5-exact-startup-commands)
6. [Dependencies and Versions](#6-dependencies-and-versions)
7. [Dataset Location and Format](#7-dataset-location-and-format)
8. [ML Model Location](#8-ml-model-location)
9. [Model Loading and Prediction Workflow](#9-model-loading-and-prediction-workflow)
10. [Parser Functionality](#10-parser-functionality)
11. [Exact Parser Output Schema with Examples](#11-exact-parser-output-schema-with-examples)
12. [Database Technology and Actual Schema](#12-database-technology-and-actual-schema)
13. [Database Initialization Instructions](#13-database-initialization-instructions)
14. [API Endpoint Documentation](#14-api-endpoint-documentation)
15. [Request and Response Examples](#15-request-and-response-examples)
16. [Upload and Analysis Workflows](#16-upload-and-analysis-workflows)
17. [Testing Instructions and Actual Results](#17-testing-instructions-and-actual-results)
18. [Known Bugs and Limitations](#18-known-bugs-and-limitations)
19. [Missing Functionality](#19-missing-functionality)
20. [Integration Instructions for Person 2](#20-integration-instructions-for-person-2)
21. [Remaining Development Tasks](#21-remaining-development-tasks)
22. [Important Configuration and Environment Variables](#22-important-configuration-and-environment-variables)
23. [Troubleshooting Instructions](#23-troubleshooting-instructions)

---

## 1. Project Overview

LogSage is an automated log anomaly detection, operational incident triage, and runbook recommendation platform designed for cloud and distributed enterprise infrastructure (specifically benchmarked on HDFS logs).

### Core Pipeline
1. **Log Ingestion & Parsing:** Raw semi-structured and unstructured logs (`.log`, `.txt`, `.csv`) are ingested and parsed in real time or batch mode using a Drain3 prefix-tree clustering engine configured with custom regex masks for IP addresses, block identifiers, hexadecimal pointers, and numbers.
2. **Block-Level Trace Aggregation & Feature Extraction:** Log lines are grouped by target entity (HDFS `BlockId`). For each block, statistical and structural features are computed (total events, template frequencies, rare templates, Shannon entropy, error/warning indicators, duration).
3. **Unsupervised Anomaly Detection:** Extracted block feature vectors are normalized using `StandardScaler` and evaluated by an ensemble `IsolationForest` model (150 trees, calibrated contamination prior ~0.04) to compute continuous anomaly scores $[0.0, 1.0]$.
4. **Automated Incident Triage & Evidence Attribution:** Blocks exceeding the anomaly threshold are persisted as `Incident` records in SQLite, along with top contributing feature explanations and raw log evidence.
5. **Semantic Runbook Retrieval:** Operational incident signatures are matched against curated Markdown runbooks using cosine similarity over embeddings (`all-MiniLM-L6-v2` / FAISS) with graceful fallback when vector search dependencies are absent.
6. **Web Dashboard Console:** A dark-mode React 18 + Vite frontend displays system health, live metrics, filterable incident tables, drill-down evidence, and triage runbooks.

---

## 2. Completed Modules

Below is the status classification of all repository modules:

| Module | Location | Implementation State | Verification State in Audit Environment |
|---|---|---|---|
| **HDFS Preprocessor** | `ml/preprocessing/hdfs_preprocessor.py` | Implemented | **Implemented & Tested** (4/4 unit tests passed in Python 3.13) |
| **Log Loader** | `ml/parser/log_loader.py` | Implemented | **Implemented & Tested** (Standard library file & string loading verified) |
| **Drain3 Log Parser** | `ml/parser/drain_parser.py` | Implemented | **Implemented but unexecuted in audit** (Requires `drain3`, previously tested by Person 1) |
| **Block Feature Extractor** | `ml/preprocessing/feature_extraction.py` | Implemented | **Implemented but unexecuted in audit** (Requires `scikit-learn`, previously tested by Person 1) |
| **Window Builder** | `ml/preprocessing/window_builder.py` | Implemented | **Implemented but unexecuted in audit** (Requires `numpy`/`pytest`, previously tested by Person 1) |
| **Isolation Forest Detector** | `ml/models/isolation_forest.py` | Implemented | **Implemented but unexecuted in audit** (Requires `scikit-learn`, previously tested by Person 1) |
| **Local Outlier Factor (LOF)** | `ml/models/lof.py` | Implemented | **Implemented but unexecuted in audit** (Baseline comparison model) |
| **ML Evaluation Suite** | `ml/evaluation/evaluate.py` | Implemented | **Implemented but unexecuted in audit** (Requires `scikit-learn`) |
| **SQLite ORM Models** | `backend/db/models.py` | Implemented | **Implemented but unexecuted in audit** (Requires `sqlalchemy`, code inspected) |
| **Database Async Engine** | `backend/db/database.py` | Implemented | **Implemented but unexecuted in audit** (Requires `sqlalchemy`, `aiosqlite`) |
| **FastAPI Backend Core** | `backend/main.py`, `backend/core/` | Implemented | **Implemented but unexecuted in audit** (Requires `fastapi`, `uvicorn`) |
| **API Schemas** | `backend/api/schemas.py` | Implemented | **Implemented but unexecuted in audit** (Requires `pydantic`) |
| **Pipeline Service** | `backend/services/pipeline_service.py` | Implemented | **Implemented but unexecuted in audit** (Requires `fastapi`, `drain3`, `scikit-learn`) |
| **REST Routes: Health** | `backend/api/routes/health.py` | Implemented | **Implemented but unexecuted in audit** (Requires running server, previously tested by Person 1) |
| **REST Routes: Logs (Upload/Analyze)** | `backend/api/routes/logs.py` | Implemented | **Implemented but unexecuted in audit** (Requires running server, previously tested by Person 1) |
| **REST Routes: Incidents** | `backend/api/routes/incidents.py` | Implemented | **Implemented but unexecuted in audit** (Requires running server, previously tested by Person 1) |
| **REST Routes: Dashboard** | `backend/api/routes/dashboard.py` | Implemented | **Implemented but unexecuted in audit** (Requires running server, previously tested by Person 1) |
| **REST Routes: Runbooks** | `backend/api/routes/runbooks.py` | Implemented | **Implemented & Code-Audited** (Graceful `ImportError` fallback added) |
| **Semantic Runbook Retrieval** | `backend/services/retrieval.py` | Partially Implemented | **Partially Implemented** (Markdown parser verified; FAISS/sentence-transformers uninstalled) |
| **Markdown Runbooks** | `runbooks/*.md` (5 runbooks) | Implemented | **Implemented & Tested** (5 files parsed and verified) |
| **Incident Status Updates (PATCH)** | `backend/api/routes/incidents.py` | Not Implemented | **Not Implemented** (Assigned to Person 2) |
| **React Ops Console** | `frontend/src/` | Implemented | **Implemented but unexecuted in audit** (Requires `node`/`npm` on host) |

---

## 3. Repository Architecture

```
LogSage/
├── backend/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── dashboard.py          # GET /api/dashboard/metrics
│   │   │   ├── health.py             # GET /health & GET /api/health
│   │   │   ├── incidents.py          # GET /api/incidents & GET /api/incidents/{id}
│   │   │   ├── logs.py               # POST /api/logs/upload & POST /api/logs/analyze
│   │   │   └── runbooks.py           # GET /api/runbooks/search & GET /api/runbooks
│   │   └── schemas.py                # Pydantic v2 schemas
│   ├── core/
│   │   ├── config.py                 # Pydantic Settings (.env configuration)
│   │   ├── exceptions.py             # Domain-specific HTTP exceptions
│   │   └── logging.py                # Structured JSON/console logger
│   ├── db/
│   │   ├── database.py               # Async SQLite engine & session factory
│   │   └── models.py                 # LogEntry, Incident, RunbookRecord ORM models
│   ├── services/
│   │   ├── ingest.py                 # File staging helper
│   │   ├── pipeline_service.py       # Orchestrates parse -> features -> ML -> DB
│   │   └── retrieval.py              # FAISS + Sentence-Transformers RAG service
│   └── main.py                       # FastAPI application & middleware entrypoint
├── data/
│   ├── processed/
│   │   ├── hdfs_data_exploration_summary.png
│   │   ├── hdfs_parsed_sample.csv    # 2,000 real parsed HDFS records
│   │   ├── hdfs_parsed_sample.json   # JSON formatted records
│   │   └── isolation_forest_evaluation.png
│   └── raw/
│       └── uploads/                  # Staging directory for file uploads
├── docs/
│   ├── API_CONTRACT.md               # API interface specification
│   ├── architecture.md               # Architectural notes
│   └── PERSON_2_HANDOFF.md           # This comprehensive handoff document
├── frontend/                         # Vite + React 18 single-page application
│   ├── src/
│   │   ├── components/
│   │   │   ├── AnomalyTable.jsx      # Filterable incident list
│   │   │   ├── LogUpload.jsx         # Upload & raw paste interface
│   │   │   ├── RunbookPanel.jsx      # Incident details & runbooks
│   │   │   └── StatusBar.jsx         # Operation indicator
│   │   ├── App.jsx                   # Main dashboard view
│   │   ├── App.css                   # NOC dark-theme CSS
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js                # Port 3000, proxies /api to port 8000
├── ml/
│   ├── evaluation/
│   │   ├── evaluate.py               # Precision, Recall, F1, AUC, PR curves
│   │   └── metrics.py
│   ├── models/
│   │   ├── base_detector.py          # Abstract anomaly detector interface
│   │   ├── isolation_forest.py       # Production Isolation Forest detector
│   │   └── lof.py                    # Local Outlier Factor baseline
│   ├── parser/
│   │   ├── drain_parser.py           # Drain3 parsing engine
│   │   ├── log_loader.py             # File and string iterator
│   │   ├── parser_config.ini         # Drain depth, similarity threshold, regex masks
│   │   └── run_hdfs_parser.py        # Standalone parser runner
│   ├── preprocessing/
│   │   ├── feature_extraction.py     # Block-level feature extractor (leakage-free)
│   │   ├── feature_extractor.py      # TF-IDF window feature extractor
│   │   ├── hdfs_preprocessor.py      # HDFS regex & trace grouping utility
│   │   └── window_builder.py         # Sliding and tumbling window builder
│   └── train_and_evaluate.py         # Full training pipeline script
├── notebooks/                        # Jupyter analysis notebooks (01 & 02)
├── runbooks/                         # Curated ops Markdown runbooks (5 files)
├── tests/                            # Pytest test suite (87 test cases)
│   ├── unit/                         # Unit tests
│   ├── integration/                  # Pipeline integration tests
│   ├── test_parser.py                # Drain3 parser test suite (13 tests)
│   ├── test_ml_pipeline.py           # ML feature & model test suite (9 tests)
│   └── test_backend_api.py           # Full API integration tests (31 tests)
├── .env.example                      # Documented configuration template
├── .gitignore                        # Git exclusion rules
├── Dockerfile.backend
├── docker-compose.yml
├── pyproject.toml                    # Pytest, ruff, mypy settings
├── requirements.txt                  # Pinned Python package dependencies
└── README.md                         # Quickstart guide
```

---

## 4. Exact Environment Setup Commands

Person 2 should execute the following commands on their local development machine:

### Backend Setup (Python 3.11+)

```bash
# 1. Navigate to repository root
cd LogSage

# 2. Create a clean project-specific virtual environment
python3 -m venv .venv

# 3. Activate the virtual environment
# On macOS / Linux:
source .venv/bin/activate
# On Windows (cmd):
# .venv\Scripts\activate.bat
# On Windows (PowerShell):
# .venv\Scripts\Activate.ps1

# 4. Upgrade pip and wheel
pip install --upgrade pip setuptools wheel

# 5. Install backend, ML, database, and testing dependencies
pip install -r requirements.txt

# 6. Copy configuration file
cp .env.example .env
```

### Optional ML Dependencies (Semantic Runbook Search)
To enable vector embedding search for runbooks:
```bash
pip install sentence-transformers==3.3.1 faiss-cpu==1.10.0
```
*(If skipped, the system operates seamlessly with graceful empty results for runbook vector search).*

### Frontend Setup (Node.js 18+)

```bash
# Navigate to frontend directory
cd frontend

# Install npm dependencies
npm install
```

---

## 5. Exact Startup Commands

### Start the FastAPI Backend

```bash
# From repository root with virtual environment activated:
source .venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Base URL: `http://localhost:8000`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- ReDoc Documentation: `http://localhost:8000/redoc`
- Health Probe: `http://localhost:8000/api/health`

### Start the React Frontend

```bash
# In a separate terminal:
cd frontend
npm run dev
```
- Web Application Console: `http://localhost:3000` (or `http://localhost:5173` depending on available ports)

---

## 6. Dependencies and Versions

From `requirements.txt`:

| Package Category | Package Name | Pinned Version | Purpose |
|---|---|---|---|
| **Web Framework** | `fastapi` | `0.115.5` | High-performance asynchronous REST API framework |
| | `uvicorn[standard]` | `0.32.1` | ASGI production server |
| | `python-multipart` | `0.0.12` | Multipart form-data parser for log file uploads |
| | `httpx` | `0.28.0` | Async and sync HTTP test client |
| **Data & ML** | `numpy` | `2.1.3` (or $\ge$ 2.0) | Numerical array processing |
| | `pandas` | `2.2.3` | Structured log transformations |
| | `scikit-learn` | `1.5.2` | Isolation Forest, StandardScaler, metrics |
| | `scipy` | `1.14.1` | Scientific routines and sparse matrices |
| **Log Parsing** | `drain3` | `0.9.11` | Online prefix-tree log template clustering |
| **Embeddings & Search** | `sentence-transformers` | `3.3.1` | Semantic text embedding generation (`all-MiniLM-L6-v2`) |
| | `faiss-cpu` | `1.10.0` | Vector similarity indexing and inner-product search |
| **Database** | `sqlalchemy` | `2.0.36` | Async ORM and query builder |
| | `aiosqlite` | `0.20.0` | Async SQLite driver |
| **Config & Tools** | `pydantic` | `2.10.2` | Request/response data validation schemas |
| | `pydantic-settings` | `2.6.1` | Environment variable management via `.env` |
| | `python-dotenv` | `1.0.1` | `.env` parser |
| | `rich` | `13.9.4` | Formatted terminal output |
| | `click` | `8.1.8` | CLI helpers |
| | `PyYAML` | `6.0.2` | YAML parser |
| **Testing & Dev** | `pytest` | `8.3.4` | Test runner |
| | `pytest-asyncio` | `0.24.0` | Asynchronous test execution |
| | `pytest-cov` | `6.0.0` | Test coverage reporting |
| | `ruff` | `0.8.1` | Fast Python linter |
| | `mypy` | `1.13.0` | Static type checker |

---

## 7. Dataset Location and Format

### Raw Dataset Directory: `data/raw/`
- `.gitignore` purposefully ignores large raw data (`data/raw/*.log`, `data/raw/*.csv`, `data/raw/*.json`) to keep the repository lightweight.
- **Reference HDFS Files:**
  - `HDFS_2k.log`: 2,000 log lines from the LogHub benchmark.
  - `HDFS_100k.log_structured.csv`: 100,000 pre-extracted events used in training notebooks.
  - `anomaly_label.csv`: Ground-truth mapping `BlockId,Label` (`Normal` vs `Anomaly`).
- **Uploads Staging:** `data/raw/uploads/` retains uploaded user files (e.g. `file-xxxx_sample.log`).

### Processed Sample Datasets: `data/processed/`
- `hdfs_parsed_sample.csv` (1.3 MB, 2,001 rows): Real structured HDFS logs parsed by `DrainParser`.
- `hdfs_parsed_sample.json` (2.1 MB): JSON-serialized representation of parsed records.

---

## 8. ML Model Location

- **Model Serialization Directory:** `ml/models/saved/`
- **Target Artifacts:**
  - `ml/models/saved/isolation_forest.joblib`: Serialized `IsolationForestDetector` state including `score_min_`, `score_max_`, `contamination`, and the underlying `scikit-learn` ensemble.
  - `ml/models/saved/feature_extractor.json`: Serialized vocabulary (`vocab_templates`), rare template set (`rare_templates`), and `StandardScaler` mean/variance.
- **Notice on Version Control:** `ml/models/saved/` is listed in `.gitignore` by default. When setting up a fresh environment, running `python ml/train_and_evaluate.py` or training on a sample generates these local artifacts so `pipeline_service.is_ml_ready` becomes `True`.

---

## 9. Model Loading and Prediction Workflow

### Initialization (`backend/services/pipeline_service.py:48-69`)
```python
model_path = Path("ml/models/saved/isolation_forest.joblib")
extractor_path = Path("ml/models/saved/feature_extractor.json")

if model_path.exists() and extractor_path.exists():
    self.detector = IsolationForestDetector.load(model_path)
    self.extractor = BlockFeatureExtractor.load(extractor_path)
```
- If artifacts are missing, the pipeline gracefully enters fallback mode (`is_ml_ready = False`). In fallback mode, logs are parsed and persisted, but anomaly inference is bypassed until model artifacts are trained.

### Prediction & Scoring (`ml/models/isolation_forest.py:92-128`)
1. **Decision Function Inversion:** `raw_scores = -self.model.decision_function(X)` (higher is more anomalous).
2. **Min-Max Normalization:**
   $$\text{score}_{\text{norm}} = \text{clip}\left(\frac{\text{raw} - \text{score}_{\text{min}}}{\text{score}_{\text{max}} - \text{score}_{\text{min}}}, 0.0, 1.0\right)$$
3. **Classification:** If a custom `threshold` is supplied, $\text{pred} = (\text{score} \ge \text{threshold})$. Otherwise, it uses the native Isolation Forest threshold calibrated with `contamination=0.04`.
4. **Feature Attribution:** Top 5 feature dimensions with the highest absolute magnitude in the standardized feature vector are recorded to explain *why* the block was isolated.

---

## 10. Parser Functionality

Implemented in `ml/parser/drain_parser.py`:
- **Engine:** Drain3 prefix-tree clustering algorithm (`TemplateMiner`).
- **Configuration (`ml/parser/parser_config.ini`):**
  - `drain_depth = 4`
  - `drain_sim_th = 0.5`
  - `max_children = 100`
  - Regex Masking:
    - `<ID>`: `blk_-?\d+`
    - `<IP>`: `(/|)([0-9]+\.){3}[0-9]+(:[0-9]+|)`
    - `<HEX>`: `\b0x[a-fA-F0-9]+\b`
    - `<NUM>`: `\b[0-9]+\b`
- **Supported Formats:**
  - HDFS Header: `YYMMDD HHMMSS <pid> <level> <component>: <content>`
  - Syslog Header: `Month Day HH:MM:SS <host> <service>[<pid>]: <content>`
  - Arbitrary line with ISO-8601 timestamp.
  - Raw unformatted strings.
- **Malformed Line Quarantine:** Empty strings or malformed lines are assigned `event_id="E0"` or `"E_ERR"`, flagged with `is_malformed=True`, and given a diagnostic `malformed_reason` without raising unhandled exceptions.

---

## 11. Exact Parser Output Schema with Examples

### Schema (`ml/parser/drain_parser.py:ParseResult`)

| Field Name | Type | Description |
|---|---|---|
| `line_id` | `int` | Sequential line identifier |
| `raw_message` | `str` | Complete original unmutated log string |
| `timestamp` | `Optional[str]` | Standardized timestamp (`YYYY-MM-DD HH:MM:SS`) |
| `level` | `Optional[str]` | Severity level (e.g., `INFO`, `ERROR`, `WARN`) |
| `component` | `Optional[str]` | Logging source component |
| `pid` | `Optional[int]` | Process ID |
| `event_id` | `str` | Mined template identifier (e.g., `E1`, `E2`) |
| `event_template` | `str` | Mined generalized template with masks |
| `content` | `str` | Message content excluding header |
| `block_ids` | `List[str]` | Extracted block identifiers (`["blk_..."]`) |
| `parameters` | `List[str]` | Extracted variable token values |
| `parameter_details` | `List[Dict[str, str]]` | Token value and mask category (`[{"value": "...", "mask_name": "..."}]`) |
| `is_new_template` | `bool` | `True` if line spawned a new cluster |
| `is_malformed` | `bool` | `True` if line was malformed or empty |
| `malformed_reason` | `Optional[str]` | Explanation if malformed |

### Actual Example Record from `data/processed/hdfs_parsed_sample.json`
```json
{
  "line_id": 1,
  "raw_message": "081109 203615 148 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_38865049064139660 terminating",
  "timestamp": "2008-11-09 20:36:15",
  "level": "INFO",
  "component": "dfs.DataNode$PacketResponder",
  "pid": 148,
  "event_id": "E1",
  "event_template": "PacketResponder <NUM> for block <ID> terminating",
  "content": "PacketResponder 1 for block blk_38865049064139660 terminating",
  "block_ids": [
    "blk_38865049064139660"
  ],
  "parameters": [
    "1",
    "blk_38865049064139660"
  ],
  "parameter_details": [
    {
      "value": "1",
      "mask_name": "NUM"
    },
    {
      "value": "blk_38865049064139660",
      "mask_name": "ID"
    }
  ],
  "is_new_template": true,
  "is_malformed": false,
  "malformed_reason": null
}
```

---

## 12. Database Technology and Actual Schema

- **Engine:** SQLite 3 with SQLAlchemy 2.0 ORM and `aiosqlite` async driver.
- **Default Database File:** `data/logsage.db`

### Tables and Columns

#### 1. `log_entries`
Stores individual parsed log lines and metadata.
- `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
- `session_id`: `VARCHAR(128)` (indexed)
- `block_id`: `VARCHAR(64)` (indexed)
- `line_number`: `INTEGER`
- `raw_line`: `TEXT NOT NULL`
- `timestamp`: `VARCHAR(64)`
- `level`: `VARCHAR(32)` (indexed)
- `component`: `VARCHAR(128)`
- `event_id`: `VARCHAR(64)` (indexed)
- `event_template`: `TEXT`
- `parameters_json`: `TEXT`
- `created_at`: `DATETIME NOT NULL`

#### 2. `incidents`
Stores flagged anomalous block events and root-cause evidence.
- `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
- `incident_id`: `VARCHAR(64) UNIQUE NOT NULL` (indexed, e.g. `INC-A1B2C3`)
- `block_id`: `VARCHAR(64) NOT NULL` (indexed)
- `title`: `VARCHAR(256) NOT NULL`
- `severity`: `VARCHAR` (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, indexed)
- `status`: `VARCHAR` (`OPEN`, `INVESTIGATING`, `RESOLVED`, indexed)
- `anomaly_score`: `FLOAT NOT NULL`
- `event_count`: `INTEGER NOT NULL`
- `top_features_json`: `TEXT` (JSON serialized feature attributions)
- `raw_evidence_json`: `TEXT` (JSON serialized list of raw log strings)
- `created_at`: `DATETIME NOT NULL` (indexed)
- `updated_at`: `DATETIME NOT NULL`

#### 3. `runbooks`
Stores metadata and index records for operations runbooks.
- `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
- `slug`: `VARCHAR(128) UNIQUE NOT NULL` (indexed)
- `title`: `VARCHAR(256) NOT NULL`
- `path`: `VARCHAR(512) NOT NULL`
- `tags`: `TEXT`
- `indexed_at`: `DATETIME NOT NULL`

---

## 13. Database Initialization Instructions

Database tables are automatically created on backend startup via the FastAPI lifespan hook (`backend/main.py:28`):
```python
await init_db()
```
To manually trigger table creation programmatically:
```python
import asyncio
from backend.db.database import init_db

asyncio.run(init_db())
print("Tables successfully verified/created in data/logsage.db")
```

---

## 14. API Endpoint Documentation

All endpoints are documented in detail in [`docs/API_CONTRACT.md`](file:///Users/heemanshusingh/Desktop/LogSage/docs/API_CONTRACT.md).

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Root health probe |
| `GET` | `/api/health` | Service liveness, SQLite connectivity, and ML status |
| `POST` | `/api/logs/upload` | Upload `.log`, `.txt`, `.csv` file (25MB limit) |
| `POST` | `/api/logs/analyze` | Parse logs, extract features, detect anomalies, create incidents |
| `GET` | `/api/incidents` | Paginated incident list with `severity` and `status` filtering |
| `GET` | `/api/incidents/{incident_id}` | Full incident details with top features, evidence, and runbooks |
| `GET` | `/api/dashboard/metrics` | System aggregates (total logs, blocks, open incidents, breakdown) |
| `GET` | `/api/runbooks` | List all available runbooks with title and excerpt |
| `GET` | `/api/runbooks/search` | Top-$k$ semantic runbook retrieval query |

---

## 15. Request and Response Examples

### Example: `POST /api/logs/analyze`
**Request:**
```bash
curl -X POST http://localhost:8000/api/logs/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "lines": [
      "081109 203615 148 INFO dfs.DataNode: Receiving block blk_101",
      "081109 203617 148 ERROR dfs.DataNode: Corrupted block blk_101 detected"
    ],
    "threshold": 0.5
  }'
```

**Response (HTTP 200 OK):**
```json
{
  "session_id": "sess-a1b2c3d4",
  "total_lines": 2,
  "total_blocks": 1,
  "anomalous_blocks": 1,
  "incidents_created": 1,
  "processing_time_ms": 14.85,
  "incidents": [
    {
      "incident_id": "INC-7F3A21",
      "block_id": "blk_101",
      "title": "Anomalous Block Activity on blk_101",
      "severity": "CRITICAL",
      "status": "OPEN",
      "anomaly_score": 0.9421,
      "event_count": 2,
      "created_at": "2026-11-18T22:30:00.123456+00:00"
    }
  ]
}
```

---

## 16. Upload and Analysis Workflows

### Staged File Workflow
1. User submits a file to `POST /api/logs/upload`.
2. Backend validates extension and file size ($\le 25\text{ MB}$), generates a unique `file_id`, and stages the file in `data/raw/uploads/`.
3. Client receives `file_id`.
4. Client invokes `POST /api/logs/analyze` with `{"session_id": "<file_id>"}`.
5. Backend loads the file from disk, runs parsing, ML detection, incident persistence, and returns results.

### Inline Raw Logs Workflow
1. Client submits raw log lines directly to `POST /api/logs/analyze` with `{"lines": ["line 1", "line 2", ...]}`.
2. Pipeline processes the array in memory and persists records with an auto-generated session identifier.

---

## 17. Testing Instructions and Actual Results

### Test Execution Commands

```bash
# 1. Run unit and ML pipeline tests (56 tests)
pytest tests/ --ignore=tests/test_backend_api.py -v

# 2. Run backend API integration tests against a live server (31 tests)
# Start server in background terminal:
uvicorn backend.main:app --host 127.0.0.1 --port 8765
# In primary terminal:
pytest tests/test_backend_api.py -v
```

### Actual Testing Results Audit

- **Total Test Cases Implemented in Repo:** 87 tests
- **Tests Executed and Passing in Current Audit Environment:**
  - `tests/unit/test_hdfs_preprocessor.py` (4 tests): **4/4 passed** (`test_block_id_regex`, `test_parse_valid_line`, `test_parse_malformed_line`, `test_group_by_block_and_labels`).
- **Tests Unexecuted in Current Audit Environment (83 tests):**
  - **Reason for Block:** The standard sandbox execution environment does not have `pytest`, `fastapi`, `uvicorn`, `scikit-learn`, `drain3`, or `aiosqlite` installed, and sandbox network isolation prevents downloading packages from PyPI via `pip install`.
  - **Unexecuted Suites:**
    - `tests/test_parser.py` (13 tests): Unexecuted in audit environment (requires `pytest`, `drain3`).
    - `tests/unit/test_parser.py` (11 tests): Unexecuted in audit environment (requires `pytest`, `drain3`).
    - `tests/test_ml_pipeline.py` (9 tests): Unexecuted in audit environment (requires `pytest`, `scikit-learn`).
    - `tests/unit/test_preprocessing.py` (8 tests): Unexecuted in audit environment (requires `pytest`, `scikit-learn`, `drain3`).
    - `tests/unit/test_anomaly.py` (11 tests): Unexecuted in audit environment (requires `pytest`, `scikit-learn`).
    - `tests/test_backend_api.py` (31 tests): Unexecuted in audit environment (requires `uvicorn` live server, `pytest`, `httpx`, `fastapi`, `aiosqlite`).
    - `tests/unit/test_retrieval.py` (retrieval tests): Unexecuted in audit environment (requires `sentence-transformers`, `faiss-cpu`).
- **Prior Verification by Person 1:**
  - On Person 1's local machine with all dependencies installed in a virtual environment, all 87 tests were reported passing (31/31 on live uvicorn server + 56/56 unit and ML tests).
  - Person 2 must set up the project `.venv` following the commands in Section 4 to run and verify the full 87-test suite.

---

## 18. Known Bugs and Limitations

1. **Vite Proxy Path Stripping (Fixed during Audit):**
   - *Previous state:* `frontend/vite.config.js` had `rewrite: (path) => path.replace(/^\/api/, '')`. Since backend routes are registered with `/api` prefixes, proxying stripped `/api` and returned 404s.
   - *Fix applied:* Removed the rewrite directive so `/api` requests forward directly to `http://localhost:8000/api/...`.
2. **Missing Runbook Search Fallback (Fixed during Audit):**
   - *Previous state:* `backend/api/routes/runbooks.py` called `retrieval_service.search` without a `try/except` guard. If `faiss-cpu` or `sentence-transformers` was uninstalled, `GET /api/runbooks/search` threw a 500 `ImportError`.
   - *Fix applied:* Guarded search with fallback returning `[]`, and updated `GET /api/runbooks` to dynamically parse markdown metadata from `runbooks/*.md`.
3. **Small Block Bias:**
   - Blocks with only 1 or 2 events are frequently flagged as outliers because typical HDFS replication traces contain 10–25 events. Person 2 can introduce an optional minimum event threshold filter (e.g., `min_events=3`) if desired.
4. **Local Model Artifacts in `.gitignore`:**
   - Because `ml/models/saved/` is gitignored, developers cloning the repository start with `is_ml_ready = False` until they generate or place the model files.

---

## 19. Missing Functionality

The following items are planned or queued for Person 2's development phase:
1. **Incident Status Mutation Endpoints:** `PATCH /api/incidents/{id}` to transition status from `OPEN` $\to$ `INVESTIGATING` $\to$ `RESOLVED`.
2. **Incident Notes / Comments:** Capability to attach human triage comments to an incident record.
3. **Batch Export Endpoint:** Exporting detected incidents to CSV or JSON from the backend.
4. **WebSocket / SSE Streaming:** Real-time log streaming directly into the frontend console.

---

## 20. Integration Instructions for Person 2

1. **Verify Backend Connectivity:**
   Start the backend and verify `http://localhost:8000/api/health` returns `{"status": "ok", "database": "ok"}`.
2. **Configure Frontend Environment:**
   Ensure `frontend/.env` contains:
   ```env
   VITE_API_URL=http://localhost:8000
   ```
3. **Connect New UI Views:**
   - Use `GET /api/incidents` for incident listing.
   - Use `GET /api/incidents/{incident_id}` to populate incident inspection drawers.
   - Use `GET /api/dashboard/metrics` for high-level NOC KPI cards.

---

## 21. Remaining Development Tasks

1. Implement `PATCH /api/incidents/{incident_id}` in `backend/api/routes/incidents.py` allowing operators to change incident severity and status.
2. Add unit tests for incident status updates in `tests/test_backend_api.py`.
3. Connect the incident status dropdown in `frontend/src/components/AnomalyTable.jsx` to the new `PATCH` endpoint.
4. Add a sample pre-trained fallback baseline model to `ml/models/saved/` or document one-click training.
5. Create Docker container orchestrations (`docker compose up --build`) for joint backend/frontend staging.

---

## 22. Important Configuration and Environment Variables

| Variable | Default Value | Description |
|---|---|---|
| `APP_ENV` | `development` | Runtime environment (`development`, `production`) |
| `APP_HOST` | `0.0.0.0` | API bind address |
| `APP_PORT` | `8000` | API port |
| `LOG_LEVEL` | `INFO` | Logger verbosity |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/logsage.db` | SQLAlchemy SQLite database connection string |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-Transformer model for runbook indexing |
| `ANOMALY_MODEL` | `isolation_forest` | ML detector algorithm identifier |
| `ANOMALY_THRESHOLD` | `0.5` | Default cutoff threshold $[0.0, 1.0]$ |
| `MODEL_SAVE_DIR` | `ml/models/saved` | Path to serialized model binaries |
| `DRAIN_DEPTH` | `4` | Drain3 prefix tree depth |
| `DRAIN_SIM_TH` | `0.4` | Drain3 cluster similarity threshold |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Allowed web browser origins |
| `VITE_API_URL` | `http://localhost:8000` | Frontend backend API URL |

---

## 23. Troubleshooting Instructions

| Symptom | Probable Cause | Solution |
|---|---|---|
| `ml_model_loaded: false` on `/api/health` | Model files missing from `ml/models/saved/` | Run `python ml/train_and_evaluate.py` or provide saved model files |
| `ModuleNotFoundError: No module named 'fastapi'` | Dependencies not installed in active environment | Activate `.venv` and run `pip install -r requirements.txt` |
| `GET /api/runbooks/search` returns `[]` | `sentence-transformers` and `faiss-cpu` not installed | Run `pip install sentence-transformers faiss-cpu` (optional) |
| Frontend displays 404 on API requests | Proxy rewrite stripping `/api` | Ensure `frontend/vite.config.js` does not rewrite `/api` |
| CORS errors in browser console | Frontend port not in `CORS_ORIGINS` | Update `CORS_ORIGINS` in `.env` or verify `settings.cors_origins_list` |
| SQLite database locked errors | Multiple synchronous test connections | Use async session and ensure `check_same_thread: False` is configured |
