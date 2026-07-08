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

    echo_sql: bool = False
    """If true, SQLAlchemy logs every SQL statement (debugging)."""


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Cached so the whole app shares one configuration. Call
    ``get_settings.cache_clear()`` in tests to force a reload.
    """
    return Settings()
