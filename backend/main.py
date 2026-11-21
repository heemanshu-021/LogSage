"""
LogSage FastAPI Application.

End-to-End Log Anomaly Detection with Runbook-Retrieval Triage API.
"""
from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routes import auth, dashboard, health, incidents, logs, runbooks
from backend.core.auth import ensure_bootstrap_account, require_authenticated_user
from backend.core.config import settings
from backend.core.logging import get_logger
from backend.core.request_limits import RequestBodyLimitMiddleware
from backend.db.database import init_db

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown lifecycle."""
    logger.info("LogSage API starting up...", env=settings.APP_ENV)
    if settings.APP_ENV == "production" and not settings.AUTH_REQUIRED:
        raise RuntimeError("AUTH_REQUIRED must be enabled when APP_ENV=production")
    await init_db()
    logger.info("SQLite database tables initialised.")
    if settings.AUTH_REQUIRED:
        await ensure_bootstrap_account()
    removed_uploads = await asyncio.to_thread(logs.cleanup_expired_uploads)
    if removed_uploads:
        logger.info("Removed expired staged uploads", count=removed_uploads)

    async def cleanup_uploads_periodically() -> None:
        while True:
            await asyncio.sleep(60 * 60)
            removed = await asyncio.to_thread(logs.cleanup_expired_uploads)
            if removed:
                logger.info("Removed expired staged uploads", count=removed)

    cleanup_task = asyncio.create_task(cleanup_uploads_periodically())
    try:
        yield
    finally:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
        logger.info("LogSage API shut down.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="LogSage API",
        description="Log Anomaly Detection with Runbook-Retrieval Triage",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.APP_ENV != "production" else None,
        redoc_url="/redoc" if settings.APP_ENV != "production" else None,
        openapi_url="/openapi.json" if settings.APP_ENV != "production" else None,
    )

    # ── CORS Middleware ────────────────────────────────────────────────────
    app.add_middleware(RequestBodyLimitMiddleware, max_bytes=27 * 1024 * 1024)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        # Origins remain explicitly allowlisted; cookies are required for local
        # account sessions and harmless when authentication is disabled.
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
    app.include_router(auth.router, prefix="/api")
    auth_guard = Depends(require_authenticated_user)
    app.include_router(logs.router, prefix="/api", dependencies=[auth_guard])
    app.include_router(incidents.router, prefix="/api", dependencies=[auth_guard])
    app.include_router(dashboard.router, prefix="/api", dependencies=[auth_guard])
    app.include_router(runbooks.router, prefix="/api/runbooks", dependencies=[auth_guard])

    return app


app = create_app()
