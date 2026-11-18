"""
LogSage FastAPI Application.

End-to-End Log Anomaly Detection with Runbook-Retrieval Triage API.
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routes import dashboard, health, incidents, logs, runbooks
from backend.core.config import settings
from backend.core.logging import get_logger
from backend.db.database import init_db

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown lifecycle."""
    logger.info("LogSage API starting up...", env=settings.APP_ENV)
    await init_db()
    logger.info("SQLite database tables initialised.")
    yield
    logger.info("LogSage API shut down.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="LogSage API",
        description="Log Anomaly Detection with Runbook-Retrieval Triage",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS Middleware ────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request Logging & Timing Middleware ────────────────────────────────
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        latency_ms = (time.perf_counter() - start) * 1000.0
        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code}",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            latency_ms=round(latency_ms, 2),
        )
        return response

    # ── Global Exception Handlers ──────────────────────────────────────────
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation Error",
                "detail": exc.errors(),
                "path": request.url.path,
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail if isinstance(exc.detail, str) else "HTTP Error",
                "detail": exc.detail,
                "status_code": exc.status_code,
                "path": request.url.path,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled server exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred during processing.",
                "path": request.url.path,
            },
        )

    # ── Router Registrations ───────────────────────────────────────────────
    # Root health probe
    app.include_router(health.router)

    # /api prefixed endpoints (contract required)
    app.include_router(health.router, prefix="/api")
    app.include_router(logs.router, prefix="/api")
    app.include_router(incidents.router, prefix="/api")
    app.include_router(dashboard.router, prefix="/api")
    app.include_router(runbooks.router, prefix="/api/runbooks")

    return app


app = create_app()
