"""Project — a body of work that advances a goal and usually has a deadline.

M0 note: the spec models Project<->Goal as many-to-many. For the foundation we
use a single primary ``goal_id`` foreign key; the join table is deferred to a
later milestone to avoid premature complexity.
"""

from __future__ import annotations

from sqlmodel import Field, SQLModel

from lifeos.models.base import TimestampMixin
from lifeos.models.enums import ProjectStatus, SourceType


class ProjectBase(SQLModel):
    title: str
    description: str | None = None
    area_id: int | None = Field(default=None, foreign_key="areas.id")
    goal_id: int | None = Field(default=None, foreign_key="goals.id")
    status: ProjectStatus = ProjectStatus.PLANNED
    priority: int = Field(default=3, ge=1, le=5)
    estimated_effort_hours: float | None = Field(default=None, ge=0.0)
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    source: SourceType = SourceType.MANUAL
    source_ref: str | None = None


class Project(ProjectBase, TimestampMixin, table=True):
    __tablename__ = "projects"

    id: int | None = Field(default=None, primary_key=True)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(SQLModel):
    title: str | None = None
    description: str | None = None
    area_id: int | None = None
    goal_id: int | None = None
    status: ProjectStatus | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    estimated_effort_hours: float | None = Field(default=None, ge=0.0)
    progress: float | None = Field(default=None, ge=0.0, le=1.0)
