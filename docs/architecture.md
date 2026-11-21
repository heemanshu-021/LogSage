# LogSage Architecture

## Current request flow

```text
React operations dashboard
  └── same-origin /api requests
      └── Nginx (container deployment: API proxy and request limits)
          └── FastAPI
              ├── POST /api/logs/upload ──> bounded, temporary upload staging
              ├── POST /api/logs/analyze
              │   ├── Drain3 parser with saved parser state
              │   ├── block grouping and block-level feature extraction
              │   ├── trained Isolation Forest and calibrated cutoff
              │   ├── SQLite log and incident persistence
              │   └── evidence-grounded triage and runbook retrieval
              ├── GET /api/incidents and /api/dashboard/metrics
              ├── GET /api/runbooks and /api/runbooks/search
              └── GET /api/health
```

## Block anomaly model

The production pipeline is `backend/services/pipeline_service.py`. It uses the fitted feature vocabulary and scaler stored alongside the saved Isolation Forest, groups parsed events by HDFS block ID, then returns block-level anomaly scores and feature attributions. The model bundle is selected with `MODEL_SAVE_DIR` and contains:

- `isolation_forest.joblib`
- `feature_extractor.json`
- `drain_state.json` and `drain_state.bin` (both are required for model readiness)

The Logfit training and evaluation implementation is in `ml/logfit_training.py`; it reads Parquet batches, writes compact aggregation state to local SQLite, and splits on block IDs before fitting transformations. See [DATASET_LOGFIT.md](DATASET_LOGFIT.md) for the split and held-out metrics.

## Data and triage

The API writes parsed log entries and incidents to SQLite. Triage uses incident evidence, the local runbook corpus, and FAISS semantic retrieval when the embedding model is available; lexical retrieval is the fallback. AI-generated investigation content is constrained by retrieved evidence and safety checks.

The former per-line `backend/api/routes/ingest.py` and `backend/services/ingest.py` path was retired because it fit a detector on first use and scored individual lines instead of using the trained block-level model. The supported ingestion flow is `/api/logs/upload` followed by `/api/logs/analyze` (or direct analysis with inline lines).

## Container routing and exposure

`docker-compose.yml` runs the API on the internal Compose network and routes the dashboard’s `/api` traffic through Nginx. The frontend port is bound to `127.0.0.1:3000` by default. Nginx applies general and analysis-specific request limits. The backend healthcheck requires a working database and loaded model bundle.

The model bundle is intentionally excluded from the Docker build context and Git. Supply the trained artifacts at `ml/models/saved/` before starting Compose; the mount is read-only. Compose enables local account authentication with an HttpOnly signed session cookie, CSRF checks on writes, and Nginx rate limits for login, analysis, and general API requests. Only the frontend is published, on loopback. For remote deployment, use TLS, set `AUTH_COOKIE_SECURE=true`, preserve client IPs only from trusted proxy networks, and keep the application behind an access proxy. The account password is never placed in browser storage; the session cookie is HttpOnly and the CSRF cookie is used only for write verification.
