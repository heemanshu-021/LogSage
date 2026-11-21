"""Request limits and staged-upload retention tests."""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.api.routes.logs import cleanup_expired_uploads
from backend.api.schemas import AnalyzeRequest, MAX_ANALYZE_LINES, MAX_LOG_LINE_CHARS
from backend.core.request_limits import RequestBodyLimitMiddleware


def test_nginx_login_slash_variants_share_strict_limit_and_canonical_upstream():
    config = (Path(__file__).resolve().parents[2] / "frontend" / "nginx.conf").read_text(encoding="utf-8")
    locations = re.findall(
        r"location\s*=\s*(/api/auth/login/?)\s*\{([^}]+)\}",
        config,
        flags=re.DOTALL,
    )

    assert {path for path, _ in locations} == {"/api/auth/login", "/api/auth/login/"}
    for _, body in locations:
        assert "limit_req zone=login_limit burst=3 nodelay;" in body
        assert "proxy_pass http://backend:8000/api/auth/login;" in body


def test_analyze_request_rejects_too_many_lines():
    with pytest.raises(ValidationError, match="too_long"):
        AnalyzeRequest(lines=["line"] * (MAX_ANALYZE_LINES + 1))


def test_analyze_request_rejects_oversized_line():
    with pytest.raises(ValidationError, match="character limit"):
        AnalyzeRequest(lines=["x" * (MAX_LOG_LINE_CHARS + 1)])


def test_expired_upload_cleanup_preserves_recent_and_unrelated_files(tmp_path: Path):
    expired = tmp_path / "file-expired_test.log"
    recent = tmp_path / "file-recent_test.log"
    unrelated = tmp_path / "keep.log"
    for path in (expired, recent, unrelated):
        path.write_text("log data", encoding="utf-8")

    expired.touch()
    os.utime(expired, (100, 100))
    os.utime(recent, (950, 950))
    os.utime(unrelated, (100, 100))

    removed = cleanup_expired_uploads(tmp_path, now=1_000, ttl_seconds=100)

    assert removed == 1
    assert not expired.exists()
    assert recent.exists()
    assert unrelated.exists()


@pytest.mark.asyncio
async def test_body_limit_middleware_rejects_chunked_oversize_body():
    async def app(scope, receive, send):
        await receive()
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    messages = iter([
        {"type": "http.request", "body": b"123456", "more_body": False},
    ])
    sent = []

    async def receive():
        return next(messages)

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/logs/analyze",
        "headers": [],
        "query_string": b"",
    }
    middleware = RequestBodyLimitMiddleware(app, max_bytes=5)
    await middleware(scope, receive, send)

    assert sent[0]["status"] == 413
    assert b"Request Too Large" in sent[1]["body"]


@pytest.mark.asyncio
async def test_body_limit_middleware_rejects_oversized_content_length_early():
    async def app(scope, receive, send):
        raise AssertionError("Oversized request should be rejected before routing")

    async def receive():
        raise AssertionError("Oversized request body should not be read")

    sent = []

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/logs/analyze",
        "headers": [(b"content-length", b"6")],
        "query_string": b"",
    }
    middleware = RequestBodyLimitMiddleware(app, max_bytes=5)
    await middleware(scope, receive, send)

    assert sent[0]["status"] == 413
    assert b"Request Too Large" in sent[1]["body"]
