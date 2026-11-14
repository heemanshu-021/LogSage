# LogSage Architecture

## System Overview

```
                 ┌────────────────────────────────────────┐
                 │            React Dashboard              │
                 │  LogUpload · AnomalyTable · RunbookPanel│
                 └──────────────────┬─────────────────────┘
                                    │ HTTP REST
                 ┌──────────────────▼─────────────────────┐
                 │             FastAPI Backend              │
                 │                                         │
                 │  POST /logs/ingest                      │
                 │  GET  /anomalies                        │
                 │  GET  /runbooks/search                  │
                 │  GET  /health                           │
                 └──────┬──────────────────┬──────────────┘
                        │                  │
         ┌──────────────▼──────┐  ┌────────▼────────────┐
         │   Ingest Service     │  │  Retrieval Service   │
         │                     │  │                      │
         │  Drain3 Parser       │  │  SentenceTransformer │
         │  FeatureExtractor    │  │  FAISS Index         │
         │  IsolationForest /   │  │  runbooks/*.md       │
         │  LOFDetector         │  │                      │
         └──────────┬──────────┘  └──────────────────────┘
                    │
         ┌──────────▼──────────┐
         │   SQLite Database   │
         │  log_entries        │
         │  anomalies          │
         │  runbooks (meta)    │
         └─────────────────────┘
```

## Component Descriptions

### Backend (FastAPI)
- **`/logs/ingest`** — Accepts raw log lines or file upload
- **`/anomalies`** — Paginates stored anomaly records
- **`/runbooks/search`** — Returns top-k semantically similar runbooks
- **`/health`** — Liveness + DB connectivity probe

### ML Pipeline
1. **Drain3 Parser** (`ml/parser/drain_parser.py`) — Extracts log templates
2. **Feature Extractor** (`ml/preprocessing/feature_extractor.py`) — TF-IDF + hand-crafted signals
3. **Anomaly Detectors** (`ml/models/`) — Isolation Forest & LOF (unsupervised)
4. **Evaluation** (`ml/evaluation/metrics.py`) — Precision/Recall/F1/AUC-ROC

### Retrieval (RAG)
- Runbooks embedded with `all-MiniLM-L6-v2` → stored in FAISS IndexFlatIP
- Cosine similarity search at query time
- Index rebuilt at startup from `runbooks/*.md`

## Data Flow

```
raw log lines
    → Drain3.add_log_message()     # template extraction
    → FeatureExtractor.transform() # TF-IDF + signals
    → IsolationForest.score()      # anomaly score [0,1]
    → SQLite (LogEntry + Anomaly)
    → GET /anomalies               # dashboard poll
    → user clicks anomaly
    → GET /runbooks/search?q=...   # FAISS cosine search
    → RunbookPanel shows top-3 hits
```

## ADR-001: Why Drain3 for Parsing

**Decision:** Use Drain3 (online log parser) over regex-based parsers.

**Rationale:**
- Drain3 is fully unsupervised — no regex rules to maintain
- Online streaming mode: no need to buffer the full log file
- State can be persisted and reloaded for incremental ingestion
- Empirically achieves >90% grouping accuracy on HDFS/BGL datasets

## ADR-002: Why Isolation Forest as Default

**Decision:** Isolation Forest as the primary detector, LOF as alternative.

**Rationale:**
- Isolation Forest scales to large datasets (O(n log n)), LOF is O(n²)
- Both are unsupervised — no labelled anomaly data required
- Isolation Forest handles high-dimensional TF-IDF features well
- LOF is offered as an alternative for dense, low-dim feature spaces
