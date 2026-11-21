"""Application configuration — loaded from .env via Pydantic Settings."""
from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/logsage.db"

    # ML / Model
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    ANOMALY_MODEL: str = "isolation_forest"
    ANOMALY_THRESHOLD: float = 0.5
    MODEL_SAVE_DIR: str = "ml/models/saved"

    # LLM / AI Incident Triage Engine
    LLM_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "openai"  # openai | gemini | generic_http
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_BASE_URL: Optional[str] = None
    LLM_TIMEOUT_SECONDS: float = 15.0
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 2000

    # Drain3 parser
    DRAIN_DEPTH: int = 4
    DRAIN_SIM_TH: float = 0.4
    DRAIN_MAX_CHILDREN: int = 100

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
