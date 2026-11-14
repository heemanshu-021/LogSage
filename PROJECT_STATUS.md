# PROJECT_STATUS.md — LogSage Live Progress Tracker

> Last updated: 2026-11-14 20:41 IST  
> Hackathon deadline: 2026-11-15 20:41 IST (24 h)

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
| `requirements.txt` | ✅ | Pinned versions |
| `README.md` | ✅ | Architecture + quickstart |
| `PROJECT_STATUS.md` | ✅ | This file |

---

## Phase 1 — Backend Foundation  `[⏳ NEXT]`

**Depends on:** Phase 0 ✅

| Task | Status | File(s) | Notes |
|------|--------|---------|-------|
| Install Python deps | ⏳ | — | `pip install -r requirements.txt` |
| `backend/core/config.py` | ⏳ | Pydantic settings from `.env` | |
| `backend/core/logging.py` | ⏳ | Structured JSON logger | |
| `backend/core/exceptions.py` | ⏳ | Custom exception hierarchy | |
| `backend/db/database.py` | ⏳ | SQLAlchemy async engine | |
| `backend/db/models.py` | ⏳ | LogEntry, Anomaly, Runbook ORM | |
| `backend/main.py` | ⏳ | FastAPI app factory | |
| `backend/api/routes/health.py` | ⏳ | GET /health | |
| Unit test: health endpoint | ⏳ | `tests/unit/test_health.py` | |

---

## Phase 2 — ML: Log Parser (Drain3)  `[🔒 Blocked on Phase 1]`

| Task | Status | File(s) | Notes |
|------|--------|---------|-------|
| `ml/parser/drain_parser.py` | 🔒 | Drain3 wrapper + template store | |
| `ml/parser/log_loader.py` | 🔒 | HDFS / syslog / custom formats | |
| Sample log data | 🔒 | `data/raw/sample.log` | HDFS or syslog |
| Unit test: parser | 🔒 | `tests/unit/test_parser.py` | |

---

## Phase 3 — ML: Preprocessing  `[🔒 Blocked on Phase 2]`

| Task | Status | File(s) | Notes |
|------|--------|---------|-------|
| `ml/preprocessing/feature_extractor.py` | 🔒 | TF-IDF / count vectors from templates | |
| `ml/preprocessing/window_builder.py` | 🔒 | Fixed / sliding window grouping | |
| `data/processed/` artifacts | 🔒 | `.npy` feature arrays | |
| Unit test: preprocessing | 🔒 | `tests/unit/test_preprocessing.py` | |

---

## Phase 4 — ML: Anomaly Detection  `[🔒 Blocked on Phase 3]`

| Task | Status | File(s) | Notes |
|------|--------|---------|-------|
| `ml/models/isolation_forest.py` | 🔒 | sklearn wrapper + serialise | |
| `ml/models/lof.py` | 🔒 | Local Outlier Factor variant | |
| `ml/models/base_detector.py` | 🔒 | Abstract base class | |
| `ml/evaluation/metrics.py` | 🔒 | Precision/Recall/F1 on labelled sets | |
| Unit test: anomaly detection | 🔒 | `tests/unit/test_anomaly.py` | |

---

## Phase 5 — Runbook Retrieval (RAG)  `[🔒 Blocked on Phase 1]`

| Task | Status | File(s) | Notes |
|------|--------|---------|-------|
| Sample runbooks (5+) | 🔒 | `runbooks/*.md` | Realistic ops runbooks |
| `backend/services/retrieval.py` | 🔒 | Embed runbooks → FAISS index | |
| `backend/api/routes/runbooks.py` | 🔒 | GET /runbooks/search | |
| Unit test: retrieval | 🔒 | `tests/unit/test_retrieval.py` | |

---

## Phase 6 — Ingest & Detection API  `[🔒 Blocked on Phase 4 + 5]`

| Task | Status | File(s) | Notes |
|------|--------|---------|-------|
| `backend/services/ingest.py` | 🔒 | Receive raw logs, parse, featurise | |
| `backend/services/anomaly_svc.py` | 🔒 | Run detector, persist results | |
| `backend/api/routes/ingest.py` | 🔒 | POST /logs/ingest | |
| `backend/api/routes/anomalies.py` | 🔒 | GET /anomalies | |
| Integration test: full pipeline | 🔒 | `tests/integration/test_pipeline.py` | |

---

## Phase 7 — React Frontend  `[🔒 Blocked on Phase 6]`

| Task | Status | File(s) | Notes |
|------|--------|---------|-------|
| Vite + React scaffold | 🔒 | `frontend/` | |
| TailwindCSS setup | 🔒 | | |
| Dashboard layout | 🔒 | `frontend/src/pages/Dashboard.jsx` | |
| Log upload component | 🔒 | `frontend/src/components/LogUpload.jsx` | |
| Anomaly table | 🔒 | `frontend/src/components/AnomalyTable.jsx` | |
| Runbook panel | 🔒 | `frontend/src/components/RunbookPanel.jsx` | |

---

## Phase 8 — Integration & Polish  `[🔒 Blocked on Phase 7]`

| Task | Status | File(s) | Notes |
|------|--------|---------|-------|
| Docker Compose | 🔒 | `docker-compose.yml` | backend + frontend |
| End-to-end smoke test | 🔒 | | |
| `docs/architecture.md` | 🔒 | Full ADR write-up | |
| Final README update | 🔒 | | |

---

## Known Issues / Blockers

_None yet — Phase 0 complete._

---

## Test Results Log

| Date/Time | Phase | Test Suite | Result | Notes |
|-----------|-------|------------|--------|-------|
| 2026-11-14 20:41 | 0 | — | — | Scaffolding only |

---

## Dependency Graph

```
Phase 0 (Scaffold)
    └── Phase 1 (Backend Core)
            ├── Phase 2 (Parser)
            │       └── Phase 3 (Preprocessing)
            │               └── Phase 4 (Anomaly Detection)
            │                       └── Phase 6 (Ingest API) ──┐
            └── Phase 5 (Runbook Retrieval) ───────────────────┘
                                                                └── Phase 7 (Frontend)
                                                                        └── Phase 8 (Integration)
```
