"""Build engine snapshots from the database and run recommendations."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlmodel import Session

from lifeos.engine import recommend_next
from lifeos.engine.balance import (
    compute_actual_allocations,
    compute_balance_drift,
)
from lifeos.engine.calibration import adjust_estimate, resolve_ratio
from lifeos.models.area import Area
from lifeos.models.completion_log import CompletionLog
from lifeos.models.goal import Goal
from lifeos.models.project import Project
from lifeos.models.task import Task
from lifeos.repositories import (
    AreaRepository,
    CalibrationRepository,
    CompletionLogRepository,
    GoalRepository,
    ProjectRepository,
    TaskRepository,
)
from lifeos.schemas.results import RecommendationResult
from lifeos.schemas.snapshot import (
    AreaSnapshot,
    CompletionLogSnapshot,
    EngineConfig,
    EngineSnapshot,
    GoalSnapshot,
    ProjectSnapshot,
    TaskSnapshot,
)


def build_snapshot(
    session: Session,
    *,
    now: datetime | None = None,
    config: EngineConfig | None = None,
) -> EngineSnapshot:
    """Load current state from the database into an engine snapshot."""
    tasks = TaskRepository(session).list(limit=500)
    goals = GoalRepository(session).list(limit=500)
    projects = ProjectRepository(session).list(limit=500)
    areas = AreaRepository(session).list(limit=100)

    cfg = config or EngineConfig()
    reference = now or datetime.now()

    cal_repo = CalibrationRepository(session)
    factors = cal_repo.list_all(limit=100)
    area_ratios = {f.area_id: f.ratio for f in factors if f.area_id is not None}
    global_factor = next((f.ratio for f in factors if f.area_id is None), 1.0)

    since = reference - timedelta(days=cfg.balance_trailing_days)
    raw_logs = CompletionLogRepository(session).list_since(since)
    completions = [_completion_snapshot(log) for log in raw_logs]

    area_snapshots = {a.id: _area_snapshot(a) for a in areas if a.id is not None}
    targets = {a.id: a.target_allocation for a in area_snapshots.values()}
    actual = compute_actual_allocations(completions)
    balance_drift = compute_balance_drift(
        target_allocations=targets,
        actual_allocations=actual,
    )

    return EngineSnapshot(
        now=reference,
        tasks=[
            _task_snapshot(t, cfg, area_ratios=area_ratios, global_ratio=global_factor)
            for t in tasks
        ],
        goals={g.id: _goal_snapshot(g) for g in goals if g.id is not None},
        projects={p.id: _project_snapshot(p) for p in projects if p.id is not None},
        areas=area_snapshots,
        completions=completions,
        area_calibration_ratios=area_ratios,
        global_calibration_ratio=global_factor,
        balance_drift=balance_drift,
        config=cfg,
    )


def recommend_now(
    session: Session,
    *,
    now: datetime | None = None,
    config: EngineConfig | None = None,
) -> RecommendationResult:
    """Load a snapshot and return the engine's recommendation."""
    snapshot = build_snapshot(session, now=now, config=config)
    return recommend_next(snapshot)


def _task_snapshot(
    task: Task,
    config: EngineConfig,
    *,
    area_ratios: dict[int, float],
    global_ratio: float,
) -> TaskSnapshot:
    assert task.id is not None
    raw = task.estimated_minutes
    if raw is None:
        raw = config.default_estimate_minutes
    ratio = resolve_ratio(task.area_id, area_ratios=area_ratios, global_ratio=global_ratio)
    calibrated = adjust_estimate(raw, ratio)
    return TaskSnapshot(
        id=task.id,
        title=task.title,
        status=task.status,
        priority=task.priority,
        estimated_minutes=calibrated,
        raw_estimated_minutes=raw,
        due_date=task.due_date,
        is_hard_deadline=task.is_hard_deadline,
        earliest_start=task.earliest_start,
        project_id=task.project_id,
        goal_id=task.goal_id,
        area_id=task.area_id,
        pinned=task.pinned,
        energy_required=task.energy_required,
        is_deep_work=task.is_deep_work,
    )


def _goal_snapshot(goal: Goal) -> GoalSnapshot:
    assert goal.id is not None
    return GoalSnapshot(
        id=goal.id,
        title=goal.title,
        priority=goal.priority,
        weight=goal.weight,
        status=goal.status,
        horizon=goal.horizon,
        progress=goal.progress,
        target_date=goal.target_date,
        area_id=goal.area_id,
    )


def _project_snapshot(project: Project) -> ProjectSnapshot:
    assert project.id is not None
    return ProjectSnapshot(
        id=project.id,
        title=project.title,
        goal_id=project.goal_id,
        area_id=project.area_id,
        priority=project.priority,
        status=project.status,
    )


def _area_snapshot(area: Area) -> AreaSnapshot:
    assert area.id is not None
    return AreaSnapshot(
        id=area.id,
        key=area.key,
        target_allocation=area.target_allocation,
    )


def _completion_snapshot(log: CompletionLog) -> CompletionLogSnapshot:
    completed = log.completed_at
    if completed.tzinfo is not None:
        completed = completed.replace(tzinfo=None)
    return CompletionLogSnapshot(
        task_id=log.task_id,
        area_id=log.area_id,
        goal_id=log.goal_id,
        estimated_minutes=log.estimated_minutes,
        actual_minutes=log.actual_minutes,
        completed_at=completed,
    )
