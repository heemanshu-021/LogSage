# LogSage — Person 2 Development Plan

> **Branch:** `main` · **Base commit:** `f51bfa3`  
> **Author:** Person 2  
> **Window:** ~12 hours  
> **Last audit:** 2026-11-18

---

## Audit Summary (Stage 1 Findings)

### Fully Implemented (Person 1)

| Module | File(s) | Status |
|---|---|---|
| Drain3 parser | `ml/parser/drain_parser.py` | ✅ Complete |
| HDFS preprocessor | `ml/preprocessing/hdfs_preprocessor.py` | ✅ Complete |
| Feature extractor (block-level) | `ml/preprocessing/feature_extraction.py` | ✅ Complete |
| Per-line feature extractor (ingest path) | `ml/preprocessing/feature_extractor.py` | ✅ Complete |
| Isolation Forest detector | `ml/models/isolation_forest.py` | ✅ Complete |
| LOF detector (alternate) | `ml/models/lof.py` | ✅ Complete |
| Base detector ABC | `ml/models/base_detector.py` | ✅ Complete |
| Evaluation metrics | `ml/evaluation/metrics.py` | ✅ Complete |
| Window builder | `ml/preprocessing/window_builder.py` | ✅ Complete |
| SQLite DB (3 tables) | `backend/db/models.py`, `database.py` | ✅ Complete |
| Pipeline service | `backend/services/pipeline_service.py` | ✅ Complete |
| Ingest service | `backend/services/ingest.py` | ✅ Present (older path, not used by current routes) |
| `POST /api/logs/upload` | `backend/api/routes/logs.py` | ✅ Complete |
| `POST /api/logs/analyze` | `backend/api/routes/logs.py` | ✅ Complete |
| `GET /api/incidents` | `backend/api/routes/incidents.py` | ✅ Complete |
| `GET /api/incidents/{id}` | `backend/api/routes/incidents.py` | ✅ Complete |
| `GET /api/dashboard/metrics` | `backend/api/routes/dashboard.py` | ✅ Complete |
| `GET /api/runbooks` | `backend/api/routes/runbooks.py` | ✅ Fixed (Prompt 6) |
| `GET /api/runbooks/search` | `backend/api/routes/runbooks.py` | ✅ Fixed (Prompt 6) |
| `GET /health`, `GET /api/health` | `backend/api/routes/health.py` | ✅ Complete |
| Runbook knowledge base (5 MDs) | `runbooks/*.md` | ✅ Complete |
| React dashboard shell | `frontend/src/App.jsx` | ✅ Complete |
| LogUpload component | `frontend/src/components/LogUpload.jsx` | ✅ Complete |
| AnomalyTable component | `frontend/src/components/AnomalyTable.jsx` | ✅ Complete |
| RunbookPanel component | `frontend/src/components/RunbookPanel.jsx` | ✅ Complete |
| Docker / docker-compose | `Dockerfile.backend`, `docker-compose.yml` | ✅ Present |

### Missing / Partially Implemented (Person 2 scope)

| Feature | Gap | Priority |
|---|---|---|
| `PATCH /api/incidents/{id}` | No status-update endpoint | **P1** |
| Incident status mutation in frontend | `AnomalyTable` has no update control; status is display-only | **P1** |
| Similar incident retrieval | No `GET /api/incidents/{id}/similar` endpoint | **P2** |
| Semantic runbook search | FAISS/sentence-transformers path exists but requires optional deps | **P2** |
| Incident triage notes | No `notes` field in DB model or API | **P3** |
| Export endpoint | No `GET /api/incidents/export` | **P3** |
| Real-time streaming | No SSE / WebSocket; polling at 15 s is in place | **P4** |
| Integration tests aligned to current routes | `tests/integration/test_pipeline.py` hits `/logs/ingest` and `/anomalies` — routes that no longer exist | **P4** |

### Critical Observation — Integration Tests Are Stale

`tests/integration/test_pipeline.py` uses:
- `POST /logs/ingest` → current route is `POST /api/logs/analyze`
- `GET /anomalies` → current route is `GET /api/incidents`
- `GET /runbooks` → current route is `GET /api/runbooks`

These tests **will fail** against the current API. They must be updated but not deleted.

---

## Environment Setup (Person 2 must run on host)

```bash
cd /Users/heemanshusingh/Desktop/LogSage

# 1. Create venv (Python 3.11+ preferred; 3.13 is acceptable)
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Train model — only if ml/models/saved/ is empty
#    Requires: data/raw/HDFS_100k.log_structured.csv + data/raw/anomaly_label.csv
python ml/train_and_evaluate.py

# 4. Start backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Start frontend (separate terminal)
cd frontend && npm install && npm run dev
```

> **Note:** `ml/models/saved/` is gitignored. If artifacts are absent the backend
> starts in fallback mode (`is_ml_ready = False`). The `/api/logs/analyze` endpoint
> still works but all blocks score 0.5 and severity is computed heuristically.

---

## Prioritised Task List

### P1 — Hours 1–2: Incident Status Updates

**Goal:** Allow operators to transition incidents `OPEN → INVESTIGATING → RESOLVED`.

**Backend changes:**

1. Add `IncidentUpdateRequest` schema to `backend/api/schemas.py`:
   ```python
   class IncidentUpdateRequest(BaseModel):
       status: str = Field(..., description="New status: OPEN, INVESTIGATING, RESOLVED")
   ```
2. Add `PATCH /api/incidents/{incident_id}` route to `backend/api/routes/incidents.py`.
3. Add `update_incident_status(incident_id, new_status, db)` method to `backend/services/pipeline_service.py`.
4. The method must:
   - Validate `new_status` is a member of `IncidentStatus` enum.
   - Set `Incident.updated_at = datetime.utcnow()`.
   - Return the updated `IncidentSummary`.

**Affected files:**
- `backend/api/schemas.py`
- `backend/api/routes/incidents.py`
- `backend/services/pipeline_service.py`

**Frontend changes:**

5. Add a status dropdown to each row in `AnomalyTable.jsx` (or to the `RunbookPanel` detail view).
6. `PATCH` to `/api/incidents/{incident_id}` on change.
7. Refresh the incidents list after a successful update.

**Tests:**
- Add `test_patch_incident_status` to `tests/test_backend_api.py`.
- Cover 200 (valid transition), 404 (not found), 422 (invalid status string).

---

### P2 — Hours 3–5: Similar Incident Retrieval + Semantic Search

#### P2a — Similar Incidents

**Goal:** `GET /api/incidents/{incident_id}/similar?top_k=5` returns incidents with the most similar feature vectors.

**Implementation:**
- Retrieve the target incident's `top_features_json` from DB.
- Compare cosine similarity against all stored incidents' feature vectors.
- Return top-k `IncidentSummary` list (excluding self).

**Affected files:**
- `backend/api/routes/incidents.py` — new sub-route
- `backend/services/pipeline_service.py` — `get_similar_incidents()` method
- `backend/api/schemas.py` — reuse `IncidentSummary`

#### P2b — Semantic Runbook Search

**Current state:** `retrieval_service.search()` requires `sentence-transformers` and `faiss-cpu`. Without them, `build_index()` silently returns without building the FAISS index and all searches return `[]`.

**Options (in order of feasibility):**

| Option | Feasibility | Description |
|---|---|---|
| Install `sentence-transformers` + `faiss-cpu` in `.venv` | ✅ Best | Full semantic search; needs network on host |
| BM25 keyword fallback | ✅ No new deps | `rank_bm25` package or manual TF-IDF over runbook text |
| substring/keyword match | ✅ Zero deps | Simple but functional; already partially in `_load_runbooks()` |

**Recommended path:** If `sentence-transformers` installs successfully, use it. If not, implement a TF-IDF keyword fallback using `sklearn` (already in `requirements.txt`) so `GET /api/runbooks/search` returns non-empty results even without FAISS.

**Affected files:**
- `backend/services/retrieval.py` — add `keyword_search()` fallback
- `backend/api/routes/runbooks.py` — call fallback when FAISS not built

---

### P3 — Hours 6–7: Incident Triage Notes

**Goal:** Let operators attach free-text notes to incidents.

**DB migration:**

```python
# In backend/db/models.py — add to Incident table:
notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
```

> SQLite does not enforce schema migrations automatically. Use `ALTER TABLE` or drop-and-recreate the DB for development. Add an Alembic migration script for production use.

**API changes:**
- Extend `PATCH /api/incidents/{incident_id}` body to accept optional `notes: Optional[str]`.
- Extend `IncidentDetail` schema to expose `notes: Optional[str]`.

**Frontend changes:**
- Add a textarea in `RunbookPanel.jsx` for `notes` when an incident is selected.
- Save on blur or explicit "Save Notes" button.

**Affected files:**
- `backend/db/models.py`
- `backend/api/schemas.py`
- `backend/api/routes/incidents.py`
- `backend/services/pipeline_service.py`
- `frontend/src/components/RunbookPanel.jsx`

---

### P4 — Hours 8–9: Export Endpoint + Fix Integration Tests

#### P4a — Export Endpoint

**Goal:** `GET /api/incidents/export?format=csv` (also `json`) downloads all incidents.

**Implementation:**
- Add route to `backend/api/routes/incidents.py`.
- Use `StreamingResponse` with `text/csv` content type for CSV.
- Fields: `incident_id, block_id, title, severity, status, anomaly_score, event_count, created_at, updated_at`.

**Affected files:**
- `backend/api/routes/incidents.py`
- `backend/api/schemas.py` (optional export-specific schema)

> **API Contract Note:** This is a new endpoint not in `docs/API_CONTRACT.md`. Document it
> and update `API_CONTRACT.md` after implementing.

#### P4b — Fix Stale Integration Tests

**Goal:** Update `tests/integration/test_pipeline.py` to use current routes.

| Old route | New route |
|---|---|
| `POST /logs/ingest` | `POST /api/logs/analyze` |
| `GET /anomalies` | `GET /api/incidents` |
| `GET /runbooks` | `GET /api/runbooks` |

Also fix response field assertions:
- `/api/logs/analyze` returns `{session_id, total_lines, total_blocks, ...}`, not `{accepted, anomalies_detected}`.
- `/api/incidents` returns `{total, limit, offset, incidents: [...]}`, not a bare list.

**Affected files:**
- `tests/integration/test_pipeline.py`

---

### P5 — Hours 10–11: Dashboard Improvements + Live Monitoring

**Goal:** Improve the React dashboard with:
1. Severity breakdown chart (bar or pie) using `metrics.severity_breakdown`.
2. Status breakdown summary in the metrics bar.
3. Configurable poll interval slider (default 15 s, range 5–60 s).
4. Visual distinction between `OPEN` / `INVESTIGATING` / `RESOLVED` rows in `AnomalyTable`.

**Affected files:**
- `frontend/src/App.jsx`
- `frontend/src/components/AnomalyTable.jsx`
- `frontend/src/App.css` (badge styles for status)

> No new npm packages required unless a chart library (e.g. `recharts`) is desired.
> Plain CSS/SVG is acceptable for MVP.

---

### P6 — Hours 12: Integration, Testing, Documentation

1. **Run full test suite:**
   ```bash
   source .venv/bin/activate
   pytest tests/ -v --tb=short 2>&1 | tee docs/test_results_person2.txt
   ```
2. **Run backend integration tests separately** (requires a running backend or ASGI client):
   ```bash
   pytest tests/test_backend_api.py tests/integration/test_pipeline.py -v
   ```
3. **Update `docs/API_CONTRACT.md`** with:
   - `PATCH /api/incidents/{incident_id}`
   - `GET /api/incidents/{incident_id}/similar`
   - `GET /api/incidents/export`
4. **Update `PROJECT_STATUS.md`** with actual test results.
5. **Git commit** with message: `feat: incident status updates, similar retrieval, export, and dashboard improvements`
6. **Push** to `origin/main`.

---

## Known Blockers

| Blocker | Impact | Workaround |
|---|---|---|
| `ml/models/saved/` artifacts not in repo | Backend starts in fallback mode; ML scoring uses heuristics | Run `python ml/train_and_evaluate.py` after getting raw data |
| Raw HDFS dataset not in repo (gitignored) | Cannot train without it | Download from [LogHub](https://github.com/logpai/loghub) |
| `sentence-transformers` / `faiss-cpu` optional deps | Semantic search returns `[]` | Implement TF-IDF keyword fallback (P2b) |
| Integration tests use stale route paths | 4 integration tests will fail | Fixed in P4b |

---

## API Contract Changes (New Endpoints)

> Do not break existing endpoints. Only add new routes.

| Method | Path | Description | Priority |
|---|---|---|---|
| `PATCH` | `/api/incidents/{incident_id}` | Update status and/or notes | P1 |
| `GET` | `/api/incidents/{incident_id}/similar` | Top-k similar incidents by feature vector | P2a |
| `GET` | `/api/incidents/export` | Download all incidents as CSV or JSON | P4a |

---

## File Change Summary

| File | Change Type | Task |
|---|---|---|
| `backend/api/schemas.py` | Add schemas | P1, P3 |
| `backend/api/routes/incidents.py` | Add PATCH, similar, export routes | P1, P2a, P4a |
| `backend/services/pipeline_service.py` | Add update_status, get_similar methods | P1, P2a |
| `backend/db/models.py` | Add `notes` column to `Incident` | P3 |
| `backend/services/retrieval.py` | Add keyword_search fallback | P2b |
| `backend/api/routes/runbooks.py` | Use keyword_search when FAISS unavailable | P2b |
| `frontend/src/components/AnomalyTable.jsx` | Status update dropdown | P1 |
| `frontend/src/components/RunbookPanel.jsx` | Notes textarea | P3 |
| `frontend/src/App.jsx` | Poll interval, severity chart | P5 |
| `tests/integration/test_pipeline.py` | Fix stale routes | P4b |
| `tests/test_backend_api.py` | Add PATCH, similar, export tests | P1, P2a, P4a |
| `docs/API_CONTRACT.md` | Document new endpoints | P6 |
| `docs/PERSON_2_DEVELOPMENT_PLAN.md` | This file | — |
