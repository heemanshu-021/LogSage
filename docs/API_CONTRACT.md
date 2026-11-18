# LogSage API Contract

> Version: 0.1.0  
> Base URL: `http://localhost:8000`  
> Content-Type: `application/json` (unless noted)  
> Author: LogSage Backend (Person 1)  
> Consumer: LogSage Frontend (Person 2)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Error Envelope](#error-envelope)
3. [GET /health](#get-health)
4. [POST /api/logs/upload](#post-apilogsupload)
5. [POST /api/logs/analyze](#post-apilogsanalyze)
6. [GET /api/incidents](#get-apiincidents)
7. [GET /api/incidents/{incident_id}](#get-apiincidentsincident_id)
8. [GET /api/incidents/{incident_id}/similar](#get-apiincidentsincident_idsimilar)
9. [GET /api/incidents/{incident_id}/runbooks](#get-apiincidentsincident_idrunbooks)
10. [GET /api/dashboard/metrics](#get-apidashboardmetrics)
11. [GET /api/runbooks](#get-apirunbooks)
12. [GET /api/runbooks/search](#get-apirunbookssearch)
13. [cURL Examples](#curl-examples)
14. [Start Backend](#start-backend)

---

## Authentication

None required for MVP. CORS is enabled for all origins (`*`) in development.

---

## Error Envelope

All error responses share a consistent JSON envelope:

```json
{
  "error": "Short error description",
  "detail": "Longer message or list of validation errors",
  "status_code": 422,
  "path": "/api/logs/analyze"
}
```

| HTTP Status | Meaning |
|-------------|---------|
| `400` | Bad request (invalid file extension, etc.) |
| `404` | Resource not found |
| `413` | File exceeds 25 MB limit |
| `422` | Validation error (missing required fields) |
| `500` | Internal server error |

---

## GET /health

Liveness probe. Returns service status, database connectivity, and ML model readiness.

**Also available at:** `GET /api/health` (identical response)

### Response `200 OK`

```json
{
  "status": "ok",
  "timestamp": "2026-11-18T08:00:00.000000+00:00",
  "database": "ok",
  "ml_model_loaded": true,
  "version": "0.1.0"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | `string` | Always `"ok"` when service is reachable |
| `timestamp` | `string` (ISO 8601 UTC) | Server time at request |
| `database` | `string` | `"ok"` or `"error"` |
| `ml_model_loaded` | `boolean` | `true` if Isolation Forest + extractor loaded |
| `version` | `string` | API version |

---

## POST /api/logs/upload

Upload a raw log file. The file is staged on disk and returns a `file_id` that can be passed to `/analyze`.

### Request

- **Content-Type:** `multipart/form-data`
- **Field:** `file` — a `.log`, `.txt`, or `.csv` file (max **25 MB**)

### Response `201 Created`

```json
{
  "file_id": "file-a1b2c3d4",
  "filename": "hdfs_server.log",
  "size_bytes": 143872,
  "total_lines": 2000,
  "message": "File 'hdfs_server.log' uploaded successfully with 2,000 lines."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `file_id` | `string` | Unique ID for this upload (pass to `/analyze` as `session_id`) |
| `filename` | `string` | Original filename |
| `size_bytes` | `integer` | File size in bytes |
| `total_lines` | `integer` | Non-empty line count |
| `message` | `string` | Human-readable confirmation |

### Error Cases

| Status | Trigger |
|--------|---------|
| `400` | Disallowed extension (not `.log`, `.txt`, `.csv`) |
| `413` | File > 25 MB |
| `422` | No file field in request |

---

## POST /api/logs/analyze

End-to-end pipeline: parse logs with Drain3 → extract block-level features → score with Isolation Forest → persist anomalous incidents to SQLite.

### Request Body

```json
{
  "lines": [
    "081109 203615 148 INFO dfs.DataNode: Receiving block blk_100 from /10.0.0.1",
    "081109 203617 148 ERROR dfs.DataNode: IOException in DataXceiver for block blk_999"
  ],
  "session_id": "file-a1b2c3d4",
  "threshold": 0.5
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `lines` | `array[string]` | **One of `lines` or `session_id`** | Raw log lines to analyze inline |
| `session_id` | `string` | Optional | `file_id` from `/upload` — loads the staged file |
| `threshold` | `float [0,1]` | Optional (default: `0.5`) | Anomaly score threshold; blocks above this are incidents |

> If both `lines` and `session_id` are supplied, `lines` take priority.

### Response `200 OK`

```json
{
  "session_id": "sess-3f8a1c2d",
  "total_lines": 12,
  "total_blocks": 5,
  "anomalous_blocks": 1,
  "incidents_created": 1,
  "processing_time_ms": 48.3,
  "incidents": [
    {
      "incident_id": "INC-A1B2C3",
      "block_id": "blk_999",
      "title": "Anomalous Block Activity on blk_999",
      "severity": "CRITICAL",
      "status": "OPEN",
      "anomaly_score": 0.8821,
      "event_count": 2,
      "created_at": "2026-11-18T08:00:01.000000+00:00"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | `string` | Session ID for this analysis run |
| `total_lines` | `integer` | Total lines received |
| `total_blocks` | `integer` | Unique Block IDs found |
| `anomalous_blocks` | `integer` | Blocks flagged as anomalous |
| `incidents_created` | `integer` | New incident records persisted |
| `processing_time_ms` | `float` | End-to-end pipeline latency in milliseconds |
| `incidents` | `array[IncidentSummary]` | Newly created incidents (see schema below) |

### Error Cases

| Status | Trigger |
|--------|---------|
| `422` | No `lines` supplied and `session_id` not found |

---

## GET /api/incidents

Paginated list of all detected incidents with optional filtering.

### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | `integer` | `50` | Page size (1–500) |
| `offset` | `integer` | `0` | Page offset |
| `severity` | `string` | — | Filter: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `status` | `string` | — | Filter: `OPEN`, `INVESTIGATING`, `RESOLVED` |

### Response `200 OK`

```json
{
  "total": 42,
  "limit": 50,
  "offset": 0,
  "incidents": [
    {
      "incident_id": "INC-A1B2C3",
      "block_id": "blk_999",
      "title": "Anomalous Block Activity on blk_999",
      "severity": "CRITICAL",
      "status": "OPEN",
      "anomaly_score": 0.8821,
      "event_count": 2,
      "created_at": "2026-11-18T08:00:01.000000+00:00"
    }
  ]
}
```

### IncidentSummary Schema

| Field | Type | Description |
|-------|------|-------------|
| `incident_id` | `string` | Unique incident identifier (`INC-XXXXXX`) |
| `block_id` | `string` | HDFS Block ID (`blk_XXXXXXXXXX`) |
| `title` | `string` | Human-readable incident title |
| `severity` | `string` | `CRITICAL` \| `HIGH` \| `MEDIUM` \| `LOW` |
| `status` | `string` | `OPEN` \| `INVESTIGATING` \| `RESOLVED` |
| `anomaly_score` | `float [0,1]` | Normalized anomaly score from Isolation Forest |
| `event_count` | `integer` | Number of log events in this block |
| `created_at` | `string` (ISO 8601 UTC) | Incident creation time |

---

## GET /api/incidents/{incident_id}

Detailed incident view with top contributing features, evidence log lines, and recommended triage runbooks.

### Path Parameters

| Param | Type | Description |
|-------|------|-------------|
| `incident_id` | `string` | Incident ID, e.g. `INC-A1B2C3` |

### Response `200 OK`

```json
{
  "incident_id": "INC-A1B2C3",
  "block_id": "blk_999",
  "title": "Anomalous Block Activity on blk_999",
  "severity": "CRITICAL",
  "status": "OPEN",
  "anomaly_score": 0.8821,
  "event_count": 2,
  "top_features": [
    { "feature": "error_count", "value": 2.0 },
    { "feature": "template_entropy", "value": 1.4142 },
    { "feature": "rare_event_freq", "value": 0.5 }
  ],
  "raw_evidence": [
    "081109 203617 148 ERROR dfs.DataNode: IOException in DataXceiver for block blk_999",
    "081109 203618 35 ERROR dfs.FSNamesystem: BLOCK NameSystem markBlockAsCorrupt blk_999"
  ],
  "recommended_runbooks": [
    {
      "slug": "hdfs-block-corruption",
      "title": "HDFS Block Corruption Runbook",
      "score": 0.912,
      "excerpt": "This runbook covers detection and recovery of corrupted HDFS blocks..."
    }
  ],
  "created_at": "2026-11-18T08:00:01.000000+00:00",
  "updated_at": "2026-11-18T08:00:01.000000+00:00"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `top_features` | `array[FeatureAttribution]` | Up to 5 features with highest absolute contribution |
| `raw_evidence` | `array[string]` | Up to 10 original log lines from this block |
| `recommended_runbooks` | `array[RunbookHit]` | Semantically matched runbooks (may be `[]` if model not loaded) |

### FeatureAttribution Schema

| Field | Type | Description |
|-------|------|-------------|
| `feature` | `string` | Feature name (e.g. `error_count`, `template_entropy`) |
| `value` | `float` | Feature value for this block |

### RunbookHit Schema

| Field | Type | Description |
|-------|------|-------------|
| `slug` | `string` | Runbook filename without extension |
| `title` | `string` | Runbook title |
| `score` | `float [0,1]` | Cosine similarity to incident description |
| `excerpt` | `string` | First 300 characters of runbook body |

### Error Cases

| Status | Trigger |
|--------|---------|
| `404` | `incident_id` not found in database |

---

## GET /api/incidents/{incident_id}/similar

Find top-k historical incidents similar to the specified incident.
Uses Sentence Transformers cosine vector similarity when available; falls back to TF-IDF lexical similarity otherwise. The target incident itself is strictly excluded from results.

### Path Parameters

| Param | Type | Description |
|-------|------|-------------|
| `incident_id` | `string` | Target incident identifier (e.g. `INC-A1B2C3`) |

### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `top_k` | `integer` | `5` | Maximum number of similar incidents to return (1–20) |

### Response `200 OK`

```json
{
  "incident_id": "INC-A1B2C3",
  "query_text": "Anomalous Block Activity on blk_999",
  "search_mode": "semantic",
  "similar_incidents": [
    {
      "incident_id": "INC-D4E5F6",
      "block_id": "blk_888",
      "title": "Anomalous Block Activity on blk_888",
      "severity": "CRITICAL",
      "status": "RESOLVED",
      "anomaly_score": 0.8654,
      "similarity_score": 0.9421,
      "search_mode": "semantic",
      "created_at": "2026-11-17T14:22:00.000000+00:00"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `incident_id` | `string` | Requested incident ID |
| `query_text` | `string` | Incident title used as similarity query |
| `search_mode` | `string` | `"semantic"` (Sentence Transformers) or `"lexical"` (TF-IDF fallback) |
| `similar_incidents` | `array[SimilarIncidentResult]` | Ranked list of similar incidents |

---

## GET /api/incidents/{incident_id}/runbooks

Retrieve top-3 relevant troubleshooting runbooks for the specified incident.
Returns full structured runbook content including Symptoms, Possible Causes, Investigation Steps, Remediation, and Verification Steps.

### Path Parameters

| Param | Type | Description |
|-------|------|-------------|
| `incident_id` | `string` | Target incident identifier (e.g. `INC-A1B2C3`) |

### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `top_k` | `integer` | `3` | Maximum number of runbooks to return (1–10) |

### Response `200 OK`

```json
{
  "incident_id": "INC-A1B2C3",
  "query_text": "Anomalous Block Activity on blk_999 error_count template_entropy",
  "search_mode": "semantic",
  "runbooks": [
    {
      "slug": "hdfs-block-corruption",
      "id": "RB-005",
      "title": "HDFS Block Corruption Recovery",
      "score": 0.912,
      "search_mode": "semantic",
      "tags": ["hdfs", "block", "corruption", "dfs"],
      "symptoms": "- `BLOCK* NameSystem.markBlockAsCorrupt` in NameNode logs...",
      "possible_causes": "1. **Underlying DataNode hardware bad sectors...**",
      "investigation_steps": "1. **Identify the corrupted block:**...",
      "remediation": "### Option A — Re-replicate from healthy replica...",
      "verification_steps": "1. Run HDFS fsck to verify corrupt blocks count is 0...",
      "escalation": "If >5% of blocks are corrupt, declare a P1 incident..."
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `incident_id` | `string` | Target incident ID |
| `query_text` | `string` | Incident description + top features used as search query |
| `search_mode` | `string` | `"semantic"` or `"lexical"` |
| `runbooks` | `array[RunbookDetailOut]` | Full structured runbooks ranked by relevance |

### Error Cases

| Status | Trigger |
|--------|---------|
| `404` | `incident_id` not found in database |

---

## GET /api/dashboard/metrics

Aggregated system-wide statistics for the operations dashboard.

### Response `200 OK`

```json
{
  "total_logs_ingested": 125000,
  "total_blocks_analyzed": 7843,
  "total_incidents": 42,
  "open_incidents": 38,
  "anomaly_rate_percent": 2.93,
  "severity_breakdown": {
    "CRITICAL": 5,
    "HIGH": 12,
    "MEDIUM": 18,
    "LOW": 7
  },
  "status_breakdown": {
    "OPEN": 38,
    "INVESTIGATING": 3,
    "RESOLVED": 1
  },
  "recent_incidents": []
}
```

| Field | Type | Description |
|-------|------|-------------|
| `total_logs_ingested` | `integer` | Total log lines ingested across all sessions |
| `total_blocks_analyzed` | `integer` | Total unique Block IDs analyzed |
| `total_incidents` | `integer` | Total incident records in database |
| `open_incidents` | `integer` | Incidents with status `OPEN` |
| `anomaly_rate_percent` | `float` | Percentage of blocks flagged as anomalous |
| `severity_breakdown` | `object` | Count by severity level |
| `status_breakdown` | `object` | Count by status |
| `recent_incidents` | `array[IncidentSummary]` | Latest 5 incidents |

---

## GET /api/runbooks

List all indexed runbooks (no semantic search, full catalogue).

### Response `200 OK`

```json
[
  {
    "slug": "hdfs-block-corruption",
    "title": "HDFS Block Corruption Runbook",
    "excerpt": "This runbook covers detection and recovery..."
  }
]
```

> Returns an empty array `[]` if `sentence-transformers` or `faiss-cpu` are not installed.

---

## GET /api/runbooks/search

Semantic search over indexed runbooks using cosine similarity.

### Query Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `q` | `string` | ✅ (min 3 chars) | Search query / anomaly description |
| `top_k` | `integer` | Optional (1–10, default `3`) | Number of results |

### Response `200 OK`

```json
[
  {
    "slug": "hdfs-block-corruption",
    "title": "HDFS Block Corruption Runbook",
    "score": 0.912,
    "excerpt": "This runbook covers detection and recovery of corrupted HDFS blocks..."
  }
]
```

> Returns `[]` if no runbooks are indexed or semantic model is unavailable.

---

## cURL Examples

### Health Check
```bash
curl http://localhost:8000/health
```

### Upload a Log File
```bash
curl -X POST http://localhost:8000/api/logs/upload \
  -F "file=@data/raw/HDFS_2k.log"
```

### Analyze Inline Log Lines
```bash
curl -X POST http://localhost:8000/api/logs/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "lines": [
      "081109 203615 148 INFO dfs.DataNode: Receiving block blk_100 from /10.0.0.1",
      "081109 203617 148 ERROR dfs.DataNode: IOException for block blk_999"
    ]
  }'
```

### Analyze Uploaded File (use file_id from upload)
```bash
curl -X POST http://localhost:8000/api/logs/analyze \
  -H "Content-Type: application/json" \
  -d '{"session_id": "file-a1b2c3d4"}'
```

### List Incidents (paginated, filtered)
```bash
curl "http://localhost:8000/api/incidents?limit=10&offset=0&severity=CRITICAL"
```

### Get Incident Detail
```bash
curl http://localhost:8000/api/incidents/INC-A1B2C3
```

### Dashboard Metrics
```bash
curl http://localhost:8000/api/dashboard/metrics
```

### Runbook Search
```bash
curl "http://localhost:8000/api/runbooks/search?q=HDFS+block+corruption&top_k=3"
```

---

## Start Backend

```bash
# From the LogSage/ project root
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Interactive docs:** http://localhost:8000/docs  
**ReDoc:** http://localhost:8000/redoc

> **Requirements:** Python 3.11+, all packages from `requirements.txt` installed, `ml/models/saved/` artifacts present.

---

## Severity Thresholds Reference

The backend assigns severity based on `anomaly_score` and presence of `ERROR`-level log events:

| Condition | Severity |
|-----------|----------|
| `score >= 0.85` **or** block has ERROR/FATAL logs | `CRITICAL` |
| `score >= 0.65` | `HIGH` |
| `score >= 0.45` | `MEDIUM` |
| `score < 0.45` | `LOW` |

---

## Notes for Frontend (Person 2)

1. **Polling:** The API is stateless. For live dashboards, poll `GET /api/dashboard/metrics` on a configurable interval (suggested: 5–30 s).
2. **File Upload Flow:** Upload with `POST /upload` → get `file_id` → trigger `POST /analyze` with `session_id: file_id`.
3. **Incident List Default Sort:** Most recent first (by `created_at` DESC).
4. **Runbook Retrieval:** Only available if `sentence-transformers` and `faiss-cpu` are installed. The `/health` endpoint's `ml_model_loaded` does **not** reflect runbook status — check if `recommended_runbooks` is `[]` in incident detail.
5. **CORS:** All origins allowed in development. Update `CORS_ORIGINS` in `.env` for production.
