"""Vault sync service."""

from __future__ import annotations

from pathlib import Path

from sqlmodel import Session

from lifeos.config import Settings, get_settings
from lifeos.ingestion.obsidian.sync import SyncResult, sync_vault


def resolve_vault_path(settings: Settings | None = None) -> Path:
    """Return the configured vault path or raise a clear error."""
    cfg = settings or get_settings()
    if cfg.vault_path is None:
        raise ValueError(
            "Vault path not configured. Set LIFEOS_VAULT_PATH in .env "
            "(e.g. /Users/scarl/Documents/AI-Vault)."
        )
    return cfg.vault_path.expanduser().resolve()


def sync_vault_from_settings(session: Session, settings: Settings | None = None) -> SyncResult:
    """Sync the configured Obsidian vault into the database."""
    return sync_vault(resolve_vault_path(settings), session)
