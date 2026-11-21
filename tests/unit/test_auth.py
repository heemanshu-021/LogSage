"""Local account password, session, and CSRF behavior."""
from __future__ import annotations

import asyncio
from pathlib import Path
import time

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.core.auth import _decode, _encode, hash_password, verify_password


def test_password_hash_is_salted_and_verified():
    encoded = hash_password("a-long-local-password")
    assert encoded != hash_password("a-long-local-password")
    assert verify_password("a-long-local-password", encoded)
    assert not verify_password("wrong-password", encoded)
    assert not verify_password("x", "malformed")


def test_signed_session_rejects_modified_payload(monkeypatch):
    from backend.core.config import settings

    monkeypatch.setattr(settings, "AUTH_SECRET_KEY", "s" * 48)
    now = int(time.time())
    encoded = _encode({"uid": 1, "sv": 0, "iat": now, "exp": now + 300})
    assert _decode(encoded)["uid"] == 1
    altered = encoded[:-1] + ("A" if encoded[-1] != "A" else "B")
    assert _decode(altered) is None


def test_production_app_disables_api_documentation(monkeypatch):
    from backend.core.config import settings
    from backend.main import create_app

    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "AUTH_REQUIRED", True)
    app = create_app()
    assert app.docs_url is None
    assert app.redoc_url is None
    assert app.openapi_url is None


@pytest.mark.asyncio
async def test_production_startup_fails_closed_without_auth(monkeypatch):
    from backend.core.config import settings
    from backend.main import app, lifespan

    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "AUTH_REQUIRED", False)
    with pytest.raises(RuntimeError, match="AUTH_REQUIRED must be enabled"):
        async with lifespan(app):
            pass


@pytest.mark.asyncio
async def test_bootstrap_creates_first_account_once(tmp_path: Path, monkeypatch):
    import backend.core.auth as auth
    from backend.core.config import settings
    from backend.db.database import Base
    from backend.db.models import User

    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'bootstrap.sqlite'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(auth, "AsyncSessionLocal", factory)
    monkeypatch.setattr(settings, "AUTH_SECRET_KEY", "bootstrap-secret-" * 3)
    monkeypatch.setattr(settings, "AUTH_ADMIN_USERNAME", "first-admin")
    monkeypatch.setattr(settings, "AUTH_ADMIN_PASSWORD", "first-admin-password")
    monkeypatch.setattr(settings, "AUTH_SESSION_TTL_SECONDS", 3600)

    await auth.ensure_bootstrap_account()
    async with factory() as session:
        user = await session.get(User, 1)
        assert user.username == "first-admin"
        assert await asyncio.to_thread(verify_password, "first-admin-password", user.password_hash)
        user.password_hash = await asyncio.to_thread(hash_password, "changed-password-value")
        await session.commit()

    await auth.ensure_bootstrap_account()
    async with factory() as session:
        user = await session.get(User, 1)
        assert await asyncio.to_thread(verify_password, "changed-password-value", user.password_hash)

    import backend.manage_accounts as account_manager
    monkeypatch.setattr(account_manager, "AsyncSessionLocal", factory)
    assert await account_manager.reset_password("first-admin", "recovered-local-password")
    async with factory() as session:
        user = await session.get(User, 1)
        assert user.session_version == 1
        assert await asyncio.to_thread(verify_password, "recovered-local-password", user.password_hash)
    await engine.dispose()


@pytest.mark.asyncio
async def test_local_login_protects_routes_and_enforces_csrf(tmp_path: Path, monkeypatch):
    from backend.core.config import settings
    from backend.db.database import Base, get_session
    from backend.db.models import User
    from backend.main import app

    monkeypatch.setattr(settings, "AUTH_REQUIRED", True)
    monkeypatch.setattr(settings, "AUTH_SECRET_KEY", "test-secret-" * 4)
    monkeypatch.setattr(settings, "AUTH_SESSION_TTL_SECONDS", 3600)
    monkeypatch.setattr(settings, "AUTH_COOKIE_SECURE", False)

    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'auth.sqlite'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_session():
        async with session_factory() as session:
            yield session

    async with session_factory() as session:
        session.add(User(username="operator", password_hash=hash_password("correct-horse-battery")))
        await session.commit()

    app.dependency_overrides[get_session] = override_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            assert (await client.get("/api/dashboard/metrics")).status_code == 401
            bad_login = await client.post(
                "/api/auth/login", json={"username": "operator", "password": "incorrect"}
            )
            assert bad_login.status_code == 401

            login = await client.post(
                "/api/auth/login", json={"username": "operator", "password": "correct-horse-battery"}
            )
            assert login.status_code == 200
            assert login.json()["authenticated"] is True
            assert "httponly" in login.headers["set-cookie"].lower()
            assert (await client.get("/api/dashboard/metrics")).status_code == 200

            blocked_write = await client.post("/api/logs/analyze", json={"lines": ["log"]})
            assert blocked_write.status_code == 403
            csrf = client.cookies.get("logsage_csrf")
            allowed_write = await client.post(
                "/api/logs/analyze",
                json={"lines": ["081109 203615 148 INFO dfs.DataNode: test block blk_800"]},
                headers={"X-CSRF-Token": csrf},
            )
            assert allowed_write.status_code == 200

            changed = await client.post(
                "/api/auth/password",
                json={"current_password": "correct-horse-battery", "new_password": "an-even-better-password"},
                headers={"X-CSRF-Token": csrf},
            )
            assert changed.status_code == 200
            assert (await client.get("/api/dashboard/metrics")).status_code == 401
            assert (await client.post(
                "/api/auth/login", json={"username": "operator", "password": "correct-horse-battery"}
            )).status_code == 401
            new_login = await client.post(
                "/api/auth/login", json={"username": "operator", "password": "an-even-better-password"}
            )
            assert new_login.status_code == 200
            csrf = client.cookies.get("logsage_csrf")

            logout = await client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf})
            assert logout.status_code == 200
            assert (await client.get("/api/dashboard/metrics")).status_code == 401
    finally:
        app.dependency_overrides.pop(get_session, None)
        await engine.dispose()
