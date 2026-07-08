"""Goal — a long-term outcome that projects and tasks advance."""

from __future__ import annotations

from datetime import date

from sqlmodel import Field, SQLModel

from lifeos.models.base import TimestampMixin
from lifeos.models.enums import GoalHorizon, GoalStatus, SourceType


class GoalBase(SQLModel):
    title: str
    description: str | None = None
    area_id: int | None = Field(default=None, foreign_key="areas.id")
    parent_goal_id: int | None = Field(default=None, foreign_key="goals.id")
    horizon: GoalHorizon = GoalHorizon.MEDIUM
    target_date: date | None = None
    priority: int = Field(default=3, ge=1, le=5, description="Human importance, 1-5.")
    weight: float = Field(
        default=0.0,
        ge=0.0,
        description="Normalized importance used by the engine (derived, overridable).",
    )
    success_criteria: str | None = None
    status: GoalStatus = GoalStatus.ACTIVE
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    source: SourceType = SourceType.MANUAL
    source_ref: str | None = None


class Goal(GoalBase, TimestampMixin, table=True):
    __tablename__ = "goals"

    id: int | None = Field(default=None, primary_key=True)


class GoalCreate(GoalBase):
    pass


class GoalUpdate(SQLModel):
    title: str | None = None
    description: str | None = None
    area_id: int | None = None
    parent_goal_id: int | None = None
    horizon: GoalHorizon | None = None
    target_date: date | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    weight: float | None = Field(default=None, ge=0.0)
    success_criteria: str | None = None
    status: GoalStatus | None = None
    progress: float | None = Field(default=None, ge=0.0, le=1.0)
