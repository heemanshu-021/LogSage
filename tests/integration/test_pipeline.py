"""Integration tests for the currently mounted LogSage API contract."""
from __future__ import annotations

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.fixture(scope="module")
async def client(tmp_path_factory):
    """Use an isolated test database and exercise the mounted /api routes."""
    from backend.db.database import Base, get_session
    from backend.main import app

    db_path: Path = tmp_path_factory.mktemp("logsage-api") / "integration.sqlite"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_session, None)
        await engine.dispose()


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
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_analyze_logs_returns_block_counts(client: AsyncClient):
    response = await client.post(
        "/api/logs/analyze",
        json={"lines": SAMPLE_LINES, "session_id": "integration-session"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_lines"] == len(SAMPLE_LINES)
    assert data["total_blocks"] == 11
    assert data["incidents_created"] == data["anomalous_blocks"]


@pytest.mark.asyncio
async def test_analyze_empty_lines_rejected(client: AsyncClient):
    response = await client.post("/api/logs/analyze", json={"lines": []})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_incidents_endpoint(client: AsyncClient):
    await client.post(
        "/api/logs/analyze",
        json={"lines": SAMPLE_LINES, "session_id": "incidents-session"},
    )
    response = await client.get("/api/incidents?limit=50")
    assert response.status_code == 200
    assert isinstance(response.json()["incidents"], list)


@pytest.mark.asyncio
async def test_runbooks_list(client: AsyncClient):
    response = await client.get("/api/runbooks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
