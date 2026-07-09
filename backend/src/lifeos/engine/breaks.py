"""Rest / day-off feasibility checks."""

from __future__ import annotations

from datetime import timedelta

from lifeos.engine.conflicts import detect_conflicts
from lifeos.engine.scoring import compute_slack_minutes, is_eligible
from lifeos.models.enums import RestVerdict
from lifeos.schemas.planning import RestResult
from lifeos.schemas.snapshot import EngineSnapshot


def evaluate_rest(
    snapshot: EngineSnapshot,
    *,
    hours: float,
) -> RestResult:
    """Determine whether taking ``hours`` off is feasible given current deadlines."""
    if hours <= 0:
        return RestResult(
            verdict=RestVerdict.YES,
            message="No time off requested.",
            hours_requested=hours,
        )

    minutes_off = int(hours * 60)
    adjusted = _snapshot_with_reduced_capacity(snapshot, minutes_off)
    conflicts = detect_conflicts(adjusted)

    infeasible = [c for c in conflicts if c.kind.value == "infeasible_deadline"]
    task_ids, min_work = _critical_tasks_after_rest(snapshot, minutes_off)

    if not infeasible and not task_ids:
        remaining = _min_slack_hours(snapshot)
        return RestResult(
            verdict=RestVerdict.YES,
            message=(
                f"Yes — you can take {hours:g}h off. "
                f"Tightest deadline still has ~{remaining:.1f}h of slack."
            ),
            hours_requested=hours,
        )

    if min_work <= minutes_off:
        return RestResult(
            verdict=RestVerdict.PARTIAL,
            message=(
                f"Partial — {hours:g}h off is tight. Do ~{min_work} min of critical work first "
                f"({len(task_ids)} task(s)), then rest."
            ),
            hours_requested=hours,
            minimum_work_minutes=min_work,
            tasks_to_clear=task_ids,
            conflicts_after_rest=infeasible,
        )

    return RestResult(
        verdict=RestVerdict.NO,
        message=(
            f"No — {hours:g}h off would miss deadlines. "
            f"You need ~{min_work} min on {len(task_ids)} critical task(s) first."
        ),
        hours_requested=hours,
        minimum_work_minutes=min_work,
        tasks_to_clear=task_ids,
        conflicts_after_rest=infeasible,
    )


def _snapshot_with_reduced_capacity(
    snapshot: EngineSnapshot,
    minutes_off: int,
) -> EngineSnapshot:
    """Simulate rest by advancing time and shrinking today's capacity."""
    config = snapshot.config.model_copy(
        update={
            "daily_capacity_minutes": max(
                1,
                snapshot.config.daily_capacity_minutes - minutes_off,
            ),
        }
    )
    return snapshot.model_copy(
        update={
            "now": snapshot.now + timedelta(minutes=minutes_off),
            "config": config,
        }
    )


def _min_slack_hours(snapshot: EngineSnapshot) -> float:
    slacks: list[float] = []
    for task in snapshot.tasks:
        if not is_eligible(task, now=snapshot.now):
            continue
        slack = compute_slack_minutes(
            task,
            now=snapshot.now,
            buffer_minutes=snapshot.config.deadline_buffer_minutes,
        )
        if slack is not None:
            slacks.append(slack / 60.0)
    return min(slacks) if slacks else 999.0


def _critical_tasks_after_rest(
    snapshot: EngineSnapshot,
    minutes_off: int,
) -> tuple[list[int], int]:
    ids: list[int] = []
    min_work = 0
    for task in snapshot.tasks:
        if not is_eligible(task, now=snapshot.now):
            continue
        slack = compute_slack_minutes(
            task,
            now=snapshot.now,
            buffer_minutes=snapshot.config.deadline_buffer_minutes,
        )
        if slack is not None and slack - minutes_off < 0:
            ids.append(task.id)
            min_work += task.estimated_minutes
    return ids, min_work
