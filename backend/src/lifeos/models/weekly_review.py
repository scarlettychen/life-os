"""WeeklyReview — structured reflection snapshot."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from lifeos.models.base import utcnow


class WeeklyReviewBase(SQLModel):
    week_start: date
    planned_vs_actual: dict = Field(default_factory=dict, sa_column=Column(JSON))
    goal_progress: dict = Field(default_factory=dict, sa_column=Column(JSON))
    energy_summary: dict = Field(default_factory=dict, sa_column=Column(JSON))
    wins: str | None = None
    misses: str | None = None
    blockers: str | None = None
    next_week_focus: str | None = None
    satisfaction: int | None = Field(default=None, ge=1, le=5)
    generated_summary: str = ""
    user_notes: str | None = None
    source_ref: str | None = None


class WeeklyReview(WeeklyReviewBase, table=True):
    __tablename__ = "weekly_reviews"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)


class WeeklyReviewCreate(WeeklyReviewBase):
    pass
