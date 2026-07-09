"""FastAPI dependency injection."""

from __future__ import annotations

from collections.abc import Generator

from sqlmodel import Session

from lifeos.db import get_engine


def get_session() -> Generator[Session, None, None]:
    """Yield a transactional database session (commit on success)."""
    session = Session(get_engine())
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
