"""Task scoring — importance, urgency, goal alignment, and time cost."""

from __future__ import annotations

from datetime import UTC, datetime

from lifeos.engine.balance import compute_balance_boost
from lifeos.models.enums import GoalStatus, TaskStatus
from lifeos.schemas.results import ScoreBreakdown
from lifeos.schemas.snapshot import (
    EngineSnapshot,
    GoalSnapshot,
    ProjectSnapshot,
    ScoringWeights,
    TaskSnapshot,
)

# Statuses excluded from ranking.
_INELIGIBLE_STATUSES = {TaskStatus.DONE, TaskStatus.DROPPED, TaskStatus.BLOCKED}


def is_eligible(task: TaskSnapshot, *, now: datetime) -> bool:
    """Return whether a task can be recommended right now."""
    if task.status in _INELIGIBLE_STATUSES:
        return False
    return task.earliest_start is None or now >= task.earliest_start


def resolve_goal_id(
    task: TaskSnapshot,
    projects: dict[int, ProjectSnapshot],
) -> int | None:
    """Best goal link: direct task link, else via project."""
    if task.goal_id is not None:
        return task.goal_id
    if task.project_id is not None:
        project = projects.get(task.project_id)
        if project is not None:
            return project.goal_id
    return None


def compute_slack_minutes(
    task: TaskSnapshot,
    *,
    now: datetime,
    buffer_minutes: int = 0,
) -> float | None:
    """Minutes of slack before the due date after accounting for effort.

    Returns ``None`` when the task has no due date.
    Negative slack means the task is already infeasible as-is.
    """
    if task.due_date is None:
        return None
    due = _as_utc(task.due_date)
    reference = _as_utc(now)
    remaining = max(task.estimated_minutes, 0)
    return (due - reference).total_seconds() / 60.0 - remaining - buffer_minutes


def compute_urgency(
    task: TaskSnapshot,
    *,
    now: datetime,
    buffer_minutes: int = 0,
) -> float:
    """Map slack to urgency in [0, 1]. Tight or negative slack → high urgency."""
    slack = compute_slack_minutes(task, now=now, buffer_minutes=buffer_minutes)
    if slack is None:
        return 0.1
    if slack <= 0:
        return 1.0
    hours = slack / 60.0
    # Smooth curve: ~1.0 at 0h slack, ~0.5 at 12h, ~0.1 at 48h+.
    return max(0.05, min(1.0, 1.0 / (1.0 + (hours / 12.0) ** 2)))


def compute_importance(
    task: TaskSnapshot,
    goals: dict[int, GoalSnapshot],
    projects: dict[int, ProjectSnapshot],
) -> float:
    """Blend task, project, and goal priority into a single importance score."""
    task_factor = task.priority / 5.0

    project_factor = 0.5
    if task.project_id is not None:
        project = projects.get(task.project_id)
        if project is not None:
            project_factor = project.priority / 5.0

    goal_factor = 0.4
    goal_id = resolve_goal_id(task, projects)
    if goal_id is not None:
        goal = goals.get(goal_id)
        if goal is not None:
            goal_factor = goal.weight if goal.weight > 0 else goal.priority / 5.0

    return min(1.0, 0.25 * task_factor + 0.25 * project_factor + 0.50 * goal_factor)


def compute_goal_alignment(
    task: TaskSnapshot,
    goals: dict[int, GoalSnapshot],
    projects: dict[int, ProjectSnapshot],
) -> float:
    """How directly this task advances an active goal."""
    goal_id = resolve_goal_id(task, projects)
    if goal_id is not None:
        goal = goals.get(goal_id)
        if goal is not None:
            if goal.status == GoalStatus.ACTIVE:
                return 1.0
            return 0.3
    if task.area_id is not None:
        return 0.4
    return 0.1


def compute_time_cost(importance: float, estimated_minutes: int) -> float:
    """Value density — important work that costs little time scores higher."""
    minutes = max(estimated_minutes, 15)
    importance_per_hour = importance / (minutes / 60.0)
    # Treat 2.0 importance/hour as excellent leverage.
    return min(1.0, importance_per_hour / 2.0)


def score_task(
    task: TaskSnapshot,
    snapshot: EngineSnapshot,
    *,
    weights: ScoringWeights | None = None,
) -> ScoreBreakdown:
    """Compute the full weighted score breakdown for one task."""
    w = weights or snapshot.config.weights
    buffer = snapshot.config.deadline_buffer_minutes

    importance = compute_importance(task, snapshot.goals, snapshot.projects)
    urgency = compute_urgency(task, now=snapshot.now, buffer_minutes=buffer)
    goal_alignment = compute_goal_alignment(task, snapshot.goals, snapshot.projects)
    time_cost = compute_time_cost(importance, task.estimated_minutes)
    slack = compute_slack_minutes(task, now=snapshot.now, buffer_minutes=buffer)
    balance = compute_balance_boost(
        task.area_id,
        snapshot.balance_drift,
        gain=snapshot.config.balance_boost_gain,
        cap=snapshot.config.balance_boost_cap,
    )

    contributions = {
        "urgency": w.urgency * urgency,
        "importance": w.importance * importance,
        "goal_alignment": w.goal_alignment * goal_alignment,
        "time_cost": w.time_cost * time_cost,
        "balance_boost": w.balance_boost * balance,
    }
    total = sum(contributions.values())

    return ScoreBreakdown(
        importance=importance,
        urgency=urgency,
        goal_alignment=goal_alignment,
        time_cost=time_cost,
        balance_boost=balance,
        slack_minutes=slack,
        weights=w,
        contributions=contributions,
        total=total,
    )


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt
