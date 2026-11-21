"""Local accounts and signed, revocable browser sessions."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.db.database import AsyncSessionLocal, get_session
from backend.db.models import User

SESSION_COOKIE = "logsage_session"
CSRF_COOKIE = "logsage_csrf"
PBKDF2_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt_hex, expected_hex = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(rounds)
        if not 100_000 <= iterations <= 2_000_000:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), iterations)
        return hmac.compare_digest(actual.hex(), expected_hex)
    except (ValueError, TypeError):
        return False


def _secret() -> bytes:
    value = settings.AUTH_SECRET_KEY
    if not value or len(value.encode("utf-8")) < 32:
        raise RuntimeError("AUTH_SECRET_KEY must contain at least 32 bytes when authentication is enabled")
    return value.encode("utf-8")


def _encode(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    body = base64.urlsafe_b64encode(raw).rstrip(b"=")
    signature = hmac.new(_secret(), body, hashlib.sha256).digest()
    return (body + b"." + base64.urlsafe_b64encode(signature).rstrip(b"=")).decode("ascii")


def _decode(token: str) -> Optional[dict]:
    try:
        body, signature = token.encode("ascii").split(b".", 1)
        expected = hmac.new(_secret(), body, hashlib.sha256).digest()
        supplied = base64.urlsafe_b64decode(signature + b"=" * (-len(signature) % 4))
        if not hmac.compare_digest(expected, supplied):
            return None
        raw = base64.urlsafe_b64decode(body + b"=" * (-len(body) % 4))
        payload = json.loads(raw)
        if not isinstance(payload, dict) or int(payload["exp"]) < int(time.time()):
            return None
        if int(payload["exp"]) - int(payload["iat"]) > settings.AUTH_SESSION_TTL_SECONDS:
            return None
        return payload
    except (ValueError, TypeError, KeyError, UnicodeError, json.JSONDecodeError, RuntimeError):
        return None


def issue_session_cookie(response, user: User) -> str:
    now = int(time.time())
    ttl = max(60, settings.AUTH_SESSION_TTL_SECONDS)
    token = _encode({"uid": user.id, "sv": user.session_version, "iat": now, "exp": now + ttl})
    csrf = secrets.token_urlsafe(32)
    options = {
        "max_age": ttl,
        "secure": settings.AUTH_COOKIE_SECURE,
        "samesite": "strict",
        "path": "/",
    }
    response.set_cookie(SESSION_COOKIE, token, httponly=True, **options)
    response.set_cookie(CSRF_COOKIE, csrf, httponly=False, **options)
    return csrf


def clear_session_cookies(response) -> None:
    for name in (SESSION_COOKIE, CSRF_COOKIE):
        response.delete_cookie(
            name,
            path="/",
            secure=settings.AUTH_COOKIE_SECURE,
            httponly=name == SESSION_COOKIE,
            samesite="strict",
        )


async def _user_from_request(request: Request, db: AsyncSession) -> Optional[User]:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    payload = _decode(token)
    if payload is None:
        return None
    try:
        user = await db.get(User, int(payload["uid"]))
        if user is None or not user.is_active or user.session_version != int(payload["sv"]):
            return None
        return user
    except (KeyError, ValueError, TypeError):
        return None


async def current_user(
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> Optional[User]:
    if not settings.AUTH_REQUIRED:
        return None
    return await _user_from_request(request, db)


async def require_authenticated_user(
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> Optional[User]:
    if not settings.AUTH_REQUIRED:
        return None
    user = await _user_from_request(request, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in required")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        cookie_token = request.cookies.get(CSRF_COOKIE, "")
        header_token = request.headers.get("X-CSRF-Token", "")
        if not cookie_token or not hmac.compare_digest(cookie_token, header_token):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token is missing or invalid")
    return user


async def ensure_bootstrap_account() -> None:
    """Create the first local account once; never reset an existing password from env."""
    _secret()
    if settings.AUTH_SESSION_TTL_SECONDS < 60:
        raise RuntimeError("AUTH_SESSION_TTL_SECONDS must be at least 60")
    async with AsyncSessionLocal() as db:
        existing = (await db.execute(select(User.id).limit(1))).first()
        if existing:
            return
        username = (settings.AUTH_ADMIN_USERNAME or "").strip()
        password = settings.AUTH_ADMIN_PASSWORD or ""
        if not username or len(username) > 128 or len(password) < 12:
            raise RuntimeError(
                "The first local account requires AUTH_ADMIN_USERNAME and an AUTH_ADMIN_PASSWORD of at least 12 characters"
            )
        user = User(username=username, password_hash=await asyncio.to_thread(hash_password, password))
        db.add(user)
        await db.commit()
