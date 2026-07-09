"""Engine output types."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from lifeos.schemas.snapshot import ScoringWeights


class ConflictKind(StrEnum):
    INFEASIBLE_DEADLINE = "infeasible_deadline"
    DAY_OVERLOAD = "day_overload"


class ScoreBreakdown(BaseModel):
    """Per-factor scores (0-1) and weighted contributions."""

    importance: float
    urgency: float
    goal_alignment: float
    time_cost: float
    balance_boost: float = 0.0
    slack_minutes: float | None = None
    weights: ScoringWeights
    contributions: dict[str, float]
    total: float


class RankedTask(BaseModel):
    task_id: int
    title: str
    score: float
    breakdown: ScoreBreakdown
    eligible: bool = True
    pinned: bool = False


class ScheduleConflict(BaseModel):
    kind: ConflictKind
    message: str
    task_ids: list[int] = Field(default_factory=list)
    due_date: str | None = None
    demand_minutes: int | None = None
    capacity_minutes: int | None = None


class RecommendationResult(BaseModel):
    """Full output of a recommendation pass."""

    ranked: list[RankedTask]
    conflicts: list[ScheduleConflict]
    top_pick: RankedTask | None = None
    eligible_count: int = 0
