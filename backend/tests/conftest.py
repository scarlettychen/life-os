"""Shared pytest fixtures.

Tests run against an isolated in-memory SQLite database so they never touch the
real ./data/lifeos.db.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

# Import models so their tables are registered on SQLModel.metadata.
import lifeos.models  # noqa: F401


@pytest.fixture
def engine() -> Iterator[Engine]:
    """A fresh in-memory database, shared across connections via StaticPool."""
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    with Session(engine) as session:
        yield session
