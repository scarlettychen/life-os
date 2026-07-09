"""Application configuration, loaded from environment / .env.

All settings use the ``LIFEOS_`` prefix (e.g. ``LIFEOS_DATABASE_URL``).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings."""

    model_config = SettingsConfigDict(
        env_prefix="LIFEOS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///data/lifeos.db"
    """SQLAlchemy database URL. Defaults to a local SQLite file under ./data."""

    vault_path: Path | None = None
    """Path to the Obsidian vault (used from M2 onwards)."""

    daily_notes_subdir: str = "Daily Notes"
    """Subdirectory under the vault where daily notes live."""

    weekly_reviews_subdir: str = "Reviews"
    """Subdirectory under the vault where weekly reviews are written."""

    brief_time: str = "07:00"
    """Local time (HH:MM) to auto-generate the daily brief."""

    review_day: str = "sun"
    """Day of week for auto weekly review (mon,tue,...,sun)."""

    review_time: str = "18:00"
    """Local time (HH:MM) for auto weekly review."""

    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    """Comma-separated allowed CORS origins for the web UI."""

    llm_provider: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None

    echo_sql: bool = False
    """If true, SQLAlchemy logs every SQL statement (debugging)."""


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Cached so the whole app shares one configuration. Call
    ``get_settings.cache_clear()`` in tests to force a reload.
    """
    return Settings()
