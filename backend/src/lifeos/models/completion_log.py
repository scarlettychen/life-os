"""CompletionLog — ground truth for estimation calibration and balance."""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel

from lifeos.models.base import utcnow


class CompletionLogBase(SQLModel):
    task_id: int = Field(foreign_key="tasks.id")
    area_id: int | None = Field(default=None, foreign_key="areas.id")
    goal_id: int | None = Field(default=None, foreign_key="goals.id")
    title: str
    estimated_minutes: int = Field(ge=0)
    actual_minutes: int = Field(ge=0)
    energy_before: float | None = Field(default=None, ge=0.0, le=1.0)
    energy_after: float | None = Field(default=None, ge=0.0, le=1.0)
    completed_at: datetime = Field(default_factory=utcnow)


class CompletionLog(CompletionLogBase, table=True):
    __tablename__ = "completion_logs"

    id: int | None = Field(default=None, primary_key=True)


class CompletionLogCreate(CompletionLogBase):
    pass
