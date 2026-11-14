"""Unit tests for /health endpoint."""
from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
async def client():
    # Use in-memory SQLite so tests don't touch the real DB
    import os
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

    from backend.main import app
    from backend.db.database import init_db
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_returns_200(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_health_schema(client: AsyncClient):
    resp = await client.get("/health")
    data = resp.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert data["database"] == "ok"
    assert data["version"] == "0.1.0"
