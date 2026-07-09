"""Engine creation and session lifecycle.

The engine is created lazily from :func:`lifeos.config.get_settings` and cached
in a module-level singleton. Tests can point at a different database via the
``LIFEOS_DATABASE_URL`` env var plus :func:`reset_engine`, or construct an
isolated engine with :func:`make_engine`.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

import lifeos.models  # noqa: F401  (register tables on SQLModel.metadata)
from lifeos.config import get_settings

_engine: Engine | None = None


def make_engine(url: str, *, echo: bool = False) -> Engine:
    """Create a new engine for ``url`` without touching the global singleton."""
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    _ensure_sqlite_dir(url)
    return create_engine(url, echo=echo, connect_args=connect_args)


def get_engine() -> Engine:
    """Return the shared engine, creating it from settings on first use."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = make_engine(settings.database_url, echo=settings.echo_sql)
    return _engine


def reset_engine() -> None:
    """Dispose and clear the cached engine (primarily for tests)."""
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None


def init_db(engine: Engine | None = None) -> None:
    """Create all tables that do not yet exist."""
    SQLModel.metadata.create_all(engine or get_engine())


@contextmanager
def session_scope(engine: Engine | None = None) -> Iterator[Session]:
    """Provide a transactional session scope.

    Commits on success, rolls back on exception, and always closes.
    """
    session = Session(engine or get_engine())
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _ensure_sqlite_dir(url: str) -> None:
    """Create the parent directory for a file-based SQLite database."""
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        return
    db_path = url[len(prefix) :]
    if not db_path or db_path == ":memory:":
        return
    Path(db_path).expanduser().parent.mkdir(parents=True, exist_ok=True)
