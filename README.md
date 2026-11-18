# LogSage 🔍🛡️

> **Production Log Anomaly Detection with Runbook-Retrieval Triage**  
> *24-Hour Hackathon MVP Architecture*

LogSage ingests raw enterprise log streams, parses them into structured event templates using an incremental **Drain3** engine, aggregates traces by HDFS Block ID, detects anomalies using a trained **Isolation Forest** model, and automatically surfaces root-cause feature attributions, raw log evidence, and matching **Ops Runbooks** via semantic search.

---

## System Architecture

```
[ Raw Log Streams / Uploads (.log, .txt, .csv) ]
                       │
                       ▼
         [ Phase 2: Drain3 Parser Engine ]
         (Depth: 4, Sim: 0.5, Regex Masks)
                       │
                       ▼
   [ Phase 3: Block Trace Feature Extractor ]
   (Total Events, Template Frequencies, Rare Events,
    Entropy, Error/Warning Indicators, Durations)
                       │
                       ▼
     [ Phase 4: Scikit-learn Isolation Forest ]
     (150 Estimators, Empirical Prior: 0.0394,
      StandardScaler, Leakage-Free Train/Test Split)
                       │
                       ▼
        [ Phase 6: FastAPI Backend + SQLite ]
  (Orchestrates Pipeline, Persists Incidents, Computes
   Live Aggregated Dashboard Metrics, CORS Middleware)
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
[ Phase 5: Runbook RAG ]   [ Phase 7: React Frontend ]
(FAISS + Sentence Transf.) (Dark-Mode Operations Console,
                            Live Metrics, Filterable Incidents,
                            Evidence Traces & Runbook Drawer)
```

---

## Directory Structure

```
LogSage/
├── backend/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── dashboard.py     # GET /api/dashboard/metrics
│   │   │   ├── health.py        # GET /health & GET /api/health
│   │   │   ├── incidents.py     # GET /api/incidents & GET /api/incidents/{id}
│   │   │   ├── logs.py          # POST /api/logs/upload & POST /api/logs/analyze
│   │   │   └── runbooks.py      # GET /api/runbooks/search & GET /api/runbooks
│   │   └── schemas.py           # Pydantic v2 validation contracts
│   ├── core/                    # Config, logging, error envelopes
│   ├── db/                      # SQLAlchemy models & SQLite async session
│   ├── services/
│   │   ├── pipeline_service.py  # End-to-end ingestion & triage singleton
│   │   └── retrieval.py         # FAISS semantic runbook retrieval
│   └── main.py                  # FastAPI application entrypoint
├── frontend/                    # React 18 + Vite dashboard
│   ├── src/
│   │   ├── components/
│   │   │   ├── AnomalyTable.jsx # Filterable incidents table
│   │   │   ├── LogUpload.jsx    # File drag-and-drop & raw paste
│   │   │   ├── RunbookPanel.jsx # Incident details, features & runbooks
│   │   │   └── StatusBar.jsx    # Live operation banner
│   │   ├── App.jsx              # Dashboard state & metrics polling
│   │   └── App.css              # Ops dark-mode styling
│   └── vite.config.js
├── ml/
│   ├── parser/                  # Drain3 parser engine & regex config
│   ├── preprocessing/           # Block trace aggregation & feature scaling
│   ├── models/                  # Isolation Forest detector & serialization
│   ├── evaluation/              # Precision/Recall/F1/AUC evaluation suite
│   └── train_and_evaluate.py    # Leakage-free benchmark training script
├── data/
│   ├── raw/                     # HDFS_2k.log, anomaly_label.csv
│   └── processed/               # Parsed CSV/JSON, evaluation PNGs
├── runbooks/                    # Markdown runbooks for automated triage
├── tests/                       # Complete Pytest test suite (87 tests)
├── notebooks/                   # Jupyter exploratory analysis notebooks
├── docs/
│   └── API_CONTRACT.md          # Exact API schemas for frontend integration
├── PROJECT_STATUS.md            # Live development progress tracker
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Prerequisites
- Python 3.11+
- Node.js 18+

### 2. Start the Backend API

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server on port 8000
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Probe:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

### 3. Start the React Frontend

```bash
cd frontend
npm install
npm run dev
```

- **Operations Dashboard:** [http://localhost:5173](http://localhost:5173)

---

## Benchmark Performance on Held-Out HDFS Test Set

Evaluated strictly on **1,588 held-out blocks** partitioned by Block ID (no data leakage):

| Metric | Score | Note |
|---|:---:|---|
| **Precision** | **1.0000** | **Zero False Alarms** (0 false positives) |
| **Specificity** | **1.0000** | 100% of normal blocks correctly identified |
| **Accuracy** | **0.9792** | 97.92% overall classification accuracy |
| **F1-Score** | **0.6452** | Conservative threshold prioritizing operational trust |
| **AUC-ROC** | **0.7289** | Discrimination capability across thresholds |
| **PR-AUC** | **0.5449** | Substantial gain over 0.0397 baseline prior |

---

## API Summary

See [docs/API_CONTRACT.md](docs/API_CONTRACT.md) for full schemas and sample responses.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Liveness, SQLite connectivity, and ML model status |
| `POST` | `/api/logs/upload` | Validate and stage `.log`/`.txt`/`.csv` files (up to 25 MB) |
| `POST` | `/api/logs/analyze` | Parse logs, extract features, run ML detector, create incidents |
| `GET` | `/api/incidents` | Paginated incident list with `severity` and `status` filters |
| `GET` | `/api/incidents/{id}` | Full incident detail with root-cause features & runbooks |
| `GET` | `/api/dashboard/metrics` | System-wide statistics: total logs, blocks, incident counts |
| `GET` | `/api/runbooks/search` | Top-k semantic search over the Ops runbooks via FAISS |
| `GET` | `/api/runbooks` | Catalog of all indexed triage runbooks |

---

## Testing

```bash
# Run Machine Learning tests (56 tests)
python -m pytest tests/ --ignore=tests/test_backend_api.py -v

# Run backend API integration tests against running server (31 tests)
# 1. Start uvicorn: uvicorn backend.main:app --host 127.0.0.1 --port 8765
# 2. Run:
python -m pytest tests/test_backend_api.py -v
```

**Total Passing Tests:** **87 / 87 (100% Pass Rate)**

---

## License

MIT
