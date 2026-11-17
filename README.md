# LogSage 🔍

> **Log Anomaly Detection with Runbook-Retrieval Triage**

LogSage ingests raw log streams, parses them into structured templates with **Drain3**, detects anomalies using **Scikit-learn** (Isolation Forest / LOF), and surfaces the top-matching **runbooks** via semantic search with **Sentence Transformers + FAISS** — all accessible through an **FastAPI** backend and a **React** dashboard..

---

## Architecture 

```
LogSage/
├── backend/          # FastAPI application
│   ├── api/          # Routes + middleware
│   ├── core/         # Config, logging, exceptions
│   ├── db/           # SQLAlchemy models + migrations
│   └── services/     # Business logic (ingest, detect, retrieve)
├── frontend/         # React dashboard (Vite)
├── ml/
│   ├── parser/       # Drain3 log template extraction
│   ├── preprocessing/# Feature engineering
│   ├── models/       # Anomaly detectors
│   └── evaluation/   # Metrics & benchmarks
├── data/
│   ├── raw/          # Incoming log files
│   └── processed/    # Featurised numpy arrays / CSVs
├── runbooks/         # Markdown runbooks for retrieval
├── tests/            # Pytest unit + integration suites
├── notebooks/        # Exploratory analysis
└── docs/             # Architecture diagrams & ADRs
```

## Quick Start

```bash
# 1. Clone & enter
git clone <repo> logsage && cd logsage

# 2. Backend
cp .env.example .env
python -m venv venv && venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn backend.main:app --reload

# 3. Frontend
cd frontend
npm install
npm run dev
```

## Development Plan

See [`PROJECT_STATUS.md`](PROJECT_STATUS.md) for the live progress tracker.

## Tech Stack

| Layer | Technology |
|---|---|
| Log Parsing | Drain3 |
| Anomaly Detection | Scikit-learn (IF, LOF), optional PyTorch Autoencoder |
| Semantic Search | Sentence Transformers + FAISS |
| Backend API | FastAPI + SQLAlchemy + SQLite |
| Frontend | React + Vite + TailwindCSS |
| Testing | Pytest + pytest-asyncio |

## License

MIT
