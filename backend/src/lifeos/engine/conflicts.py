"""Scheduling conflict detection — deterministic feasibility checks."""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from lifeos.engine.scoring import compute_slack_minutes, is_eligible
from lifeos.schemas.results import ConflictKind, ScheduleConflict
from lifeos.schemas.snapshot import EngineSnapshot, TaskSnapshot


def detect_conflicts(
    snapshot: EngineSnapshot,
    *,
    tasks: list[TaskSnapshot] | None = None,
) -> list[ScheduleConflict]:
    """Find deadline infeasibility and same-day overload among eligible tasks."""
    pool = tasks if tasks is not None else snapshot.tasks
    eligible = [t for t in pool if is_eligible(t, now=snapshot.now)]

    conflicts: list[ScheduleConflict] = []
    conflicts.extend(_infeasible_deadlines(eligible, snapshot))
    conflicts.extend(_day_overloads(eligible, snapshot))
    return conflicts


def _infeasible_deadlines(
    tasks: list[TaskSnapshot],
    snapshot: EngineSnapshot,
) -> list[ScheduleConflict]:
    buffer = snapshot.config.deadline_buffer_minutes
    results: list[ScheduleConflict] = []

    for task in tasks:
        if task.due_date is None:
            continue
        slack = compute_slack_minutes(
            task, now=snapshot.now, buffer_minutes=buffer
        )
        if slack is not None and slack < 0:
            hours_over = abs(slack) / 60.0
            results.append(
                ScheduleConflict(
                    kind=ConflictKind.INFEASIBLE_DEADLINE,
                    message=(
                        f"'{task.title}' cannot finish before its deadline "
                        f"({hours_over:.1f}h short even starting now)."
                    ),
                    task_ids=[task.id],
                    due_date=task.due_date.isoformat(),
                    demand_minutes=task.estimated_minutes,
                )
            )
    return results


def _day_overloads(
    tasks: list[TaskSnapshot],
    snapshot: EngineSnapshot,
) -> list[ScheduleConflict]:
    capacity = snapshot.config.daily_capacity_minutes
    by_day: dict[date, list[TaskSnapshot]] = defaultdict(list)

    for task in tasks:
        if task.due_date is None:
            continue
        by_day[task.due_date.date()].append(task)

    results: list[ScheduleConflict] = []
    for day, day_tasks in sorted(by_day.items()):
        demand = sum(t.estimated_minutes for t in day_tasks)
        if demand <= capacity:
            continue
        titles = ", ".join(f"'{t.title}'" for t in day_tasks[:3])
        if len(day_tasks) > 3:
            titles += f" (+{len(day_tasks) - 3} more)"
        results.append(
            ScheduleConflict(
                kind=ConflictKind.DAY_OVERLOAD,
                message=(
                    f"{day.isoformat()}: {demand} min of work due but only "
                    f"{capacity} min capacity ({titles})."
                ),
                task_ids=[t.id for t in day_tasks],
                due_date=day.isoformat(),
                demand_minutes=demand,
                capacity_minutes=capacity,
            )
        )
    return results
