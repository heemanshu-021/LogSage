# LogSage 🔍🛡️

> **Production Log Anomaly Detection with Runbook-Retrieval Triage**  
> *24-Hour Hackathon MVP Architecture*

LogSage ingests raw enterprise log streams, parses them into structured event templates using an incremental **Drain3** engine, aggregates traces by HDFS Block ID, detects anomalies using a trained **Isolation Forest** model, and automatically surfaces root-cause feature attributions, raw log evidence, and matching **Ops Runbooks** via semantic search.

## HackBriven × Serverpod challenge integration

The selected track is **Here, together**: responders can create or join authenticated, real-time incident rooms in the Serverpod Flutter web app under `logsage_cloud/`. Rooms share participant updates and persisted incident notes across connected responders. Run locally with the Serverpod development setup documented in [`docs/SERVERPOD_MIGRATION.md`](docs/SERVERPOD_MIGRATION.md). This is an additive collaboration app; it does not yet replace the existing React/FastAPI dashboard or its ML pipeline. Deployment is intentionally deferred until requested.

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
     (150 Estimators, Training Prior: 0.02924,
      Training-Fit StandardScaler, Block-Isolated Train/Validation/Test)
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
- Node.js 20.19+ or 22.12+ (required by Vite 8)

### 2. Start the Backend API

```bash
# Install Python dependencies
pip install -r requirements.txt

# If you do not already have .env, copy .env.example to .env. Set a private
# AUTH_SECRET_KEY and the unique AUTH_ADMIN_PASSWORD (at least 12 characters).
# Generate a secret with: python -c "import secrets; print(secrets.token_urlsafe(48))"

# Start the FastAPI server on port 8000
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Probe:** [http://localhost:8000/api/health](http://localhost:8000/api/health)
- Local account sign-in is controlled by `AUTH_REQUIRED`. On an empty database, `AUTH_ADMIN_USERNAME` and `AUTH_ADMIN_PASSWORD` create the first account once. Remove the bootstrap password from `.env` afterward. Keep the 32+ character `AUTH_SECRET_KEY` and `.env` private.
- Sessions use HttpOnly, SameSite cookies with CSRF checks; passwords are stored as salted PBKDF2 hashes. Public self-registration is disabled. A signed-in local user can change their password through `POST /api/auth/password`.
- If the password is forgotten, run `python -m backend.manage_accounts reset-password <username>` from the repository root; it prompts without echoing the password and revokes existing sessions.

### 3. Start the React Frontend

```bash
cd frontend
npm install
npm run dev
```

On Windows PowerShell, if the execution policy blocks `npm.ps1`, use `npm.cmd install` and `npm.cmd run dev`. If Vite is reported as missing, install the frontend dependencies first with `npm.cmd install` from the `frontend` folder.

- **Operations Dashboard:** [http://localhost:3000](http://localhost:3000)
- The Vite development server proxies `/api` to `http://localhost:8000`. To use another local backend port, set `VITE_API_PROXY_TARGET` before `npm run dev`.
- For a cross-origin deployment, set `VITE_API_URL` at build time and add the frontend origin to backend `CORS_ORIGINS`.
- Staged upload files expire after 24 hours and are cleaned at startup and hourly while the API runs.

---

## Logfit HDFS_v1 Benchmark

Evaluated on **114,803 held-out blocks** from the five-shard Logfit HDFS_v1 dataset. Blocks are assigned deterministically to 70% train, 10% validation, and 20% test before fitting the feature vocabulary or scaler. The validation split selects the decision cutoff; the test split remains held out.

| Metric | Score | Note |
|---|:---:|---|
| **Precision** | **0.7622** | 2,911 true positives and 908 false positives |
| **Recall** | **0.8659** | 2,911 of 3,362 anomalous blocks detected |
| **Specificity** | **0.9919** | 110,533 of 111,441 normal blocks identified |
| **Accuracy** | **0.9882** | 113,444 of 114,803 blocks correct |
| **F1-Score** | **0.8108** | Validation-selected cutoff |
| **AUC-ROC** | **0.9942** | Ranking across all score cutoffs |
| **PR-AUC** | **0.7927** | Test anomaly prior: 2.93% |

Full counts, split metadata, and artifact paths are in [docs/DATASET_LOGFIT.md](docs/DATASET_LOGFIT.md) and `data/processed/logfit_training_report.json`.

## Optional Container Deployment

This deployment option is separate from the normal local workflow. For local development, run FastAPI and Vite directly as described in Quick Start; Vite forwards `/api` requests to the backend.

The Compose deployment keeps the API on its private Docker network, routes same-origin `/api` traffic through Nginx, applies request limits at that proxy, and binds the dashboard to `127.0.0.1:3000` by default. The API healthcheck stays unhealthy until SQLite and the trained model are both ready.

The model bundle is intentionally excluded from Git and the Docker build context. Train it with the command above or securely copy a compatible release bundle into `ml/models/saved/` before starting Compose. First copy `.env.example` to `.env`, replace `AUTH_SECRET_KEY` with a random value (for example, `python -c "import secrets; print(secrets.token_urlsafe(48))"`), and set a unique admin username and password of at least 12 characters. The first local account is created only when the database has no accounts. Remove `AUTH_ADMIN_PASSWORD` (and the one-time username setting if desired) after that first successful creation; later starts will not reset existing accounts. Keep `.env` private.

```bash
docker compose up --build
```

The frontend remains bound to `127.0.0.1:3000`; the backend container port is internal to Compose. Local account sign-in protects application routes; health remains available for probes and API documentation is disabled in production. For remote access, set `AUTH_COOKIE_SECURE=true`, use TLS, and publish only behind an identity-aware access proxy. Preserve real client addresses only from trusted proxy networks. Do not expose the frontend or backend directly to the public internet.

---

## API Summaries

See [docs/API_CONTRACT.md](docs/API_CONTRACT.md) for full schemas and sample responses.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Liveness, SQLite connectivity, and ML model status |
| `GET` | `/api/auth/session` | Check whether sign-in is required and the current local session |
| `POST` | `/api/auth/login` | Sign in to the configured local account |
| `POST` | `/api/auth/logout` | Revoke local sessions and sign out |
| `POST` | `/api/auth/password` | Change the signed-in local account password |
| `POST` | `/api/logs/upload` | Validate and stage `.log`/`.txt`/`.csv` files (up to 25 MiB, 100,000 lines, 16,384 characters per line) |
| `POST` | `/api/logs/analyze` | Parse and score up to 100,000 lines (16,384 characters per line), then create incidents |
| `GET` | `/api/incidents` | Paginated incident list with `severity` and `status` filters |
| `GET` | `/api/incidents/{id}` | Full incident detail with root-cause features & runbooks |
| `GET` | `/api/dashboard/metrics` | System-wide statistics: total logs, blocks, incident counts |
| `GET` | `/api/runbooks/search` | Top-k semantic search over the Ops runbooks via FAISS |
| `GET` | `/api/runbooks` | Catalog of all indexed triage runbooks |

---

## Training and testing

Train the Logfit model after installing `requirements.txt` and downloading the dataset:

```bash
python scripts/download_logfit_dataset.py
python ml/train_and_evaluate.py --dataset logfit
```

The historical CSV training path remains available with `--dataset legacy`.

## Testing

```bash
# Run unit and integration tests, excluding the live-server API suite
python -m pytest tests/ --ignore=tests/test_backend_api.py -v

# Run backend API integration tests against running server (31 tests)
# 1. Start uvicorn: uvicorn backend.main:app --host 127.0.0.1 --port 8765
# 2. Run:
python -m pytest tests/test_backend_api.py -v
```

Latest verification on the current `main` commit: **218 backend/ML tests passed and 1 skipped** in the broad non-server suite, **34/34 live-server API tests passed**, and auth coverage includes bootstrap, password hashing, protected requests, CSRF, password rotation/reset, revocation, and production startup settings. A live browser session also signed in to the local account, loaded the dashboard with ML ready, and signed out successfully. The frontend production build and lint both pass. Docker/Nginx are optional deployment files and are not required for local use. See `PROJECT_PROGRESS.md` for details.

---

## License

MIT
