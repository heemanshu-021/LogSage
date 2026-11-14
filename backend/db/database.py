"""SQLAlchemy async engine + session factory."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.core.config import settings

# SQLite requires the aiosqlite driver prefix
_db_url = settings.DATABASE_URL
if _db_url.startswith("sqlite:///") and "aiosqlite" not in _db_url:
    _db_url = _db_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

engine = create_async_engine(
    _db_url,
    connect_args={"check_same_thread": False},
    echo=settings.APP_ENV == "development",
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


async def init_db() -> None:
    """Create all tables (idempotent)."""
    # Import models so their metadata is registered
    import backend.db.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:  # type: ignore[return]
    """FastAPI dependency — yields an async DB session."""
    async with AsyncSessionLocal() as session:
        yield session
