"""Task — the atomic actionable unit the decision engine ranks."""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel

from lifeos.models.base import TimestampMixin
from lifeos.models.enums import EnergyLevel, SourceType, TaskStatus


class TaskBase(SQLModel):
    title: str
    notes: str | None = None

    project_id: int | None = Field(default=None, foreign_key="projects.id")
    goal_id: int | None = Field(default=None, foreign_key="goals.id")
    area_id: int | None = Field(default=None, foreign_key="areas.id")

    status: TaskStatus = TaskStatus.TODO
    priority: int = Field(default=3, ge=1, le=5)
    estimated_minutes: int | None = Field(default=None, ge=0)
    actual_minutes: int | None = Field(default=None, ge=0)

    due_date: datetime | None = None
    is_hard_deadline: bool = False
    earliest_start: datetime | None = None

    energy_required: EnergyLevel = EnergyLevel.MEDIUM
    is_deep_work: bool = False
    pinned: bool = False

    completed_at: datetime | None = None
    source: SourceType = SourceType.MANUAL
    source_ref: str | None = None


class Task(TaskBase, TimestampMixin, table=True):
    __tablename__ = "tasks"

    id: int | None = Field(default=None, primary_key=True)


class TaskCreate(TaskBase):
    pass


class TaskUpdate(SQLModel):
    title: str | None = None
    notes: str | None = None
    project_id: int | None = None
    goal_id: int | None = None
    area_id: int | None = None
    status: TaskStatus | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    estimated_minutes: int | None = Field(default=None, ge=0)
    actual_minutes: int | None = Field(default=None, ge=0)
    due_date: datetime | None = None
    is_hard_deadline: bool | None = None
    earliest_start: datetime | None = None
    energy_required: EnergyLevel | None = None
    is_deep_work: bool | None = None
    pinned: bool | None = None
    completed_at: datetime | None = None
