"""TimeBlock — a scheduled instance of work on the calendar."""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel

from lifeos.models.base import TimestampMixin
from lifeos.models.enums import TimeBlockKind, TimeBlockStatus


class TimeBlockBase(SQLModel):
    task_id: int | None = Field(default=None, foreign_key="tasks.id")
    title: str
    start: datetime
    end: datetime
    status: TimeBlockStatus = TimeBlockStatus.PROPOSED
    kind: TimeBlockKind = TimeBlockKind.WORK
    rationale: str | None = None


class TimeBlock(TimeBlockBase, TimestampMixin, table=True):
    __tablename__ = "time_blocks"

    id: int | None = Field(default=None, primary_key=True)


class TimeBlockCreate(TimeBlockBase):
    pass
