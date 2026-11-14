"""LogSage Backend — Application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.core.logging import get_logger
from backend.db.database import init_db
from backend.api.routes import health, ingest, anomalies, runbooks

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("LogSage starting up…", env=settings.APP_ENV)
    await init_db()
    logger.info("Database initialised.")
    yield
    logger.info("LogSage shutting down.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="LogSage API",
        description="Log Anomaly Detection with Runbook-Retrieval Triage",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, tags=["Health"])
    app.include_router(ingest.router, prefix="/logs", tags=["Ingest"])
    app.include_router(anomalies.router, prefix="/anomalies", tags=["Anomalies"])
    app.include_router(runbooks.router, prefix="/runbooks", tags=["Runbooks"])

    return app


app = create_app()
