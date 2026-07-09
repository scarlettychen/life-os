"""Immutable snapshot types consumed by the pure decision engine."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from lifeos.models.enums import EnergyLevel, GoalHorizon, GoalStatus, ProjectStatus, TaskStatus


class CompletionLogSnapshot(BaseModel):
    """Completion record used by balance and velocity logic."""

    task_id: int
    area_id: int | None = None
    goal_id: int | None = None
    estimated_minutes: int = Field(ge=0)
    actual_minutes: int = Field(ge=0)
    completed_at: datetime


class TaskSnapshot(BaseModel):
    """Actionable task state at a point in time."""

    id: int
    title: str
    status: TaskStatus
    priority: int = Field(ge=1, le=5)
    estimated_minutes: int = Field(default=60, ge=0)
    raw_estimated_minutes: int | None = Field(
        default=None,
        ge=0,
        description="Un-calibrated estimate before area ratio is applied.",
    )
    due_date: datetime | None = None
    is_hard_deadline: bool = False
    earliest_start: datetime | None = None
    project_id: int | None = None
    goal_id: int | None = None
    area_id: int | None = None
    pinned: bool = False
    energy_required: EnergyLevel = EnergyLevel.MEDIUM
    is_deep_work: bool = False


class GoalSnapshot(BaseModel):
    id: int
    title: str
    priority: int = Field(ge=1, le=5)
    weight: float = Field(default=0.0, ge=0.0)
    status: GoalStatus = GoalStatus.ACTIVE
    horizon: GoalHorizon = GoalHorizon.MEDIUM
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    target_date: date | None = None
    area_id: int | None = None


class ProjectSnapshot(BaseModel):
    id: int
    title: str
    goal_id: int | None = None
    area_id: int | None = None
    priority: int = Field(ge=1, le=5)
    status: ProjectStatus = ProjectStatus.ACTIVE


class AreaSnapshot(BaseModel):
    id: int
    key: str
    target_allocation: float = Field(default=0.0, ge=0.0, le=1.0)


class ScoringWeights(BaseModel):
    """Weights for ranking factors (should sum to ~1.0)."""

    urgency: float = 0.30
    importance: float = 0.25
    goal_alignment: float = 0.20
    time_cost: float = 0.15
    balance_boost: float = 0.10


class EngineConfig(BaseModel):
    """Tunable knobs for scoring and conflict detection."""

    weights: ScoringWeights = Field(default_factory=ScoringWeights)
    deadline_buffer_minutes: int = Field(
        default=0,
        ge=0,
        description="Safety buffer subtracted from slack before urgency is computed.",
    )
    daily_capacity_minutes: int = Field(
        default=240,
        ge=1,
        description="Discretionary work minutes available per day (conflict detection).",
    )
    default_estimate_minutes: int = Field(default=60, ge=1)
    # Scheduling (M3)
    day_start_hour: int = Field(default=7, ge=0, le=23)
    day_end_hour: int = Field(default=22, ge=1, le=24)
    slot_minutes: int = Field(default=15, ge=5, le=60)
    min_rest_minutes: int = Field(default=60, ge=0)
    daily_deep_work_cap_minutes: int = Field(default=240, ge=0)
    break_after_deep_work_minutes: int = Field(default=10, ge=0)
    calibration_ema_alpha: float = Field(default=0.3, gt=0.0, le=1.0)
    balance_trailing_days: int = Field(default=7, ge=1)
    balance_boost_gain: float = Field(default=1.0, ge=0.0)
    balance_boost_cap: float = Field(default=0.15, ge=0.0, le=1.0)


class EngineSnapshot(BaseModel):
    """Everything the engine needs to rank tasks and detect conflicts."""

    now: datetime
    tasks: list[TaskSnapshot]
    goals: dict[int, GoalSnapshot] = Field(default_factory=dict)
    projects: dict[int, ProjectSnapshot] = Field(default_factory=dict)
    areas: dict[int, AreaSnapshot] = Field(default_factory=dict)
    completions: list[CompletionLogSnapshot] = Field(default_factory=list)
    area_calibration_ratios: dict[int, float] = Field(default_factory=dict)
    global_calibration_ratio: float = Field(default=1.0, ge=0.1, le=5.0)
    balance_drift: dict[int, float] = Field(default_factory=dict)
    config: EngineConfig = Field(default_factory=EngineConfig)
