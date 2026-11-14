"""Integration test — full log ingest pipeline."""
from __future__ import annotations

import os
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture(scope="module", autouse=True)
def set_test_db():
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="module")
async def client():
    from backend.main import app
    from backend.db.database import init_db
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


SAMPLE_LINES = [
    "081109 203615 148 INFO dfs.DataNode: Receiving block blk_100 from /10.0.0.1",
    "081109 203616 148 INFO dfs.DataNode: Receiving block blk_101 from /10.0.0.2",
    "081109 203617 148 ERROR dfs.DataNode: IOException in DataXceiver for block blk_999",
    "081109 203618 35 ERROR dfs.FSNamesystem: BLOCK NameSystem markBlockAsCorrupt blk_999",
    "081109 203619 148 INFO dfs.DataNode: Receiving block blk_102 from /10.0.0.3",
    "081109 203620 148 INFO dfs.DataNode: Receiving block blk_103 from /10.0.0.4",
    "081109 203621 148 INFO dfs.DataNode: Receiving block blk_104 from /10.0.0.5",
    "081109 203622 148 INFO dfs.DataNode: Receiving block blk_105 from /10.0.0.6",
    "081109 203623 35 WARN dfs.DataNode: Slow I/O for block blk_200",
    "081109 203624 148 INFO dfs.DataNode: Receiving block blk_106 from /10.0.0.7",
    "081109 203625 148 INFO dfs.DataNode: Receiving block blk_107 from /10.0.0.8",
    "081109 203626 148 INFO dfs.DataNode: Receiving block blk_108 from /10.0.0.9",
]


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_ingest_returns_accepted(client: AsyncClient):
    resp = await client.post(
        "/logs/ingest",
        json={"lines": SAMPLE_LINES, "source": "api", "session_id": "test-session-1"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["accepted"] == len(SAMPLE_LINES)
    assert "anomalies_detected" in data


@pytest.mark.asyncio
async def test_ingest_empty_lines_rejected(client: AsyncClient):
    resp = await client.post("/logs/ingest", json={"lines": []})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_anomalies_endpoint(client: AsyncClient):
    # Ensure we have ingested data first
    await client.post(
        "/logs/ingest",
        json={"lines": SAMPLE_LINES, "source": "api", "session_id": "test-session-2"},
    )
    resp = await client.get("/anomalies?limit=50")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_runbooks_list(client: AsyncClient):
    resp = await client.get("/runbooks")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
