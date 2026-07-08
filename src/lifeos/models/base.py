"""Shared model building blocks."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    """Timezone-aware current UTC time (used for created/updated stamps)."""
    return datetime.now(UTC)


class TimestampMixin(SQLModel):
    """Adds ``created_at`` / ``updated_at`` to a table model.

    ``updated_at`` is bumped explicitly by the repository layer on writes.
    """

    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)
