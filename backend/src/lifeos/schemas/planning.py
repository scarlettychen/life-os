"""Planning and scheduling result types."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from lifeos.models.enums import RestVerdict, TimeBlockKind, TimeBlockStatus
from lifeos.schemas.results import RecommendationResult, ScheduleConflict


class PlannedBlock(BaseModel):
    """A proposed time block from the scheduler."""

    task_id: int | None
    title: str
    start: datetime
    end: datetime
    status: TimeBlockStatus = TimeBlockStatus.PROPOSED
    kind: TimeBlockKind = TimeBlockKind.WORK
    rationale: str
    energy_fit: float = Field(ge=0.0, le=1.0)


class DayPlanResult(BaseModel):
    """Output of a daily scheduling pass."""

    blocks: list[PlannedBlock]
    recommendation: RecommendationResult
    conflicts: list[ScheduleConflict]
    unscheduled_task_ids: list[int] = Field(default_factory=list)
    total_scheduled_minutes: int = 0
    deep_work_minutes: int = 0


class RestResult(BaseModel):
    """Output of a rest-feasibility check."""

    verdict: RestVerdict
    message: str
    hours_requested: float
    minimum_work_minutes: int = 0
    tasks_to_clear: list[int] = Field(default_factory=list)
    conflicts_after_rest: list[ScheduleConflict] = Field(default_factory=list)
