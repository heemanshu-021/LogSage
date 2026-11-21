"""Local account sign-in and session management."""
from __future__ import annotations

import asyncio
import secrets

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import (
    clear_session_cookies,
    current_user,
    hash_password,
    issue_session_cookie,
    require_authenticated_user,
    verify_password,
)
from backend.core.config import settings
from backend.db.database import get_session
from backend.db.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])
_dummy_password_hash = hash_password(secrets.token_urlsafe(32))


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=1024)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=1024)
    new_password: str = Field(min_length=12, max_length=1024)


@router.get("/session")
async def get_session_status(user: User | None = Depends(current_user)):
    return {
        "auth_required": settings.AUTH_REQUIRED,
        "authenticated": user is not None if settings.AUTH_REQUIRED else True,
        "username": user.username if user else None,
    }


@router.post("/login")
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_session),
):
    if not settings.AUTH_REQUIRED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local account sign-in is disabled")
    normalized_username = payload.username.strip()
    result = await db.execute(select(User).where(User.username == normalized_username))
    user = result.scalar_one_or_none()
    encoded = user.password_hash if user is not None else _dummy_password_hash
    valid_password = await asyncio.to_thread(verify_password, payload.password, encoded)
    if user is None or not user.is_active or not valid_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    issue_session_cookie(response, user)
    return {"authenticated": True, "username": user.username}


@router.post("/logout")
async def logout(
    response: Response,
    user: User | None = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_session),
):
    if user is not None:
        user.session_version += 1
        await db.commit()
    clear_session_cookies(response)
    return {"authenticated": False}


@router.post("/password")
async def change_password(
    payload: PasswordChangeRequest,
    response: Response,
    user: User | None = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_session),
):
    if user is None or not await asyncio.to_thread(verify_password, payload.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")
    user.password_hash = await asyncio.to_thread(hash_password, payload.new_password)
    user.session_version += 1
    await db.commit()
    clear_session_cookies(response)
    return {"authenticated": False, "password_changed": True}
