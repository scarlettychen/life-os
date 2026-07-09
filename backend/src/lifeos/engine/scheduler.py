"""Greedy, deadline-aware, energy-aware day scheduler."""

from __future__ import annotations

from datetime import datetime, timedelta

from lifeos.engine.energy import energy_fit
from lifeos.engine.recommend import recommend_next
from lifeos.engine.scoring import is_eligible
from lifeos.engine.slots import FreeSlot, build_free_slots, day_horizon_end
from lifeos.models.enums import TimeBlockKind, TimeBlockStatus
from lifeos.schemas.planning import DayPlanResult, PlannedBlock
from lifeos.schemas.snapshot import EngineSnapshot, TaskSnapshot


def plan_day(snapshot: EngineSnapshot) -> DayPlanResult:
    """Build a proposed schedule for the rest of today."""
    recommendation = recommend_next(snapshot)
    horizon_end = day_horizon_end(snapshot.now, snapshot.config)
    slots = build_free_slots(
        now=snapshot.now,
        horizon_end=horizon_end,
        config=snapshot.config,
    )

    task_by_id = {t.id: t for t in snapshot.tasks}
    ranked_ids = [r.task_id for r in recommendation.ranked]
    blocks: list[PlannedBlock] = []
    unscheduled: list[int] = []
    deep_work_used = 0
    cap = snapshot.config.daily_deep_work_cap_minutes

    for task_id in ranked_ids:
        task = task_by_id.get(task_id)
        if task is None or not is_eligible(task, now=snapshot.now):
            continue
        if task.is_deep_work and deep_work_used >= cap:
            unscheduled.append(task_id)
            continue

        placement = _place_task(task, slots, snapshot.now)
        if placement is None:
            unscheduled.append(task_id)
            continue

        start, end, fit, used_indices = placement
        for idx in used_indices:
            slots[idx].used = True

        if task.is_deep_work:
            deep_work_used += task.estimated_minutes

        rationale = _rationale(task, fit, snapshot.now)
        blocks.append(
            PlannedBlock(
                task_id=task.id,
                title=task.title,
                start=start,
                end=end,
                kind=TimeBlockKind.WORK,
                rationale=rationale,
                energy_fit=fit,
            )
        )

        if task.is_deep_work and snapshot.config.break_after_deep_work_minutes > 0:
            _maybe_insert_break(blocks, slots, task, snapshot.config.break_after_deep_work_minutes)

    total_minutes = sum(int((b.end - b.start).total_seconds() / 60) for b in blocks)
    deep_minutes = sum(
        int((b.end - b.start).total_seconds() / 60)
        for b in blocks
        if b.task_id is not None
        and (t := task_by_id.get(b.task_id)) is not None
        and t.is_deep_work
    )

    return DayPlanResult(
        blocks=sorted(blocks, key=lambda b: b.start),
        recommendation=recommendation,
        conflicts=recommendation.conflicts,
        unscheduled_task_ids=unscheduled,
        total_scheduled_minutes=total_minutes,
        deep_work_minutes=deep_minutes,
    )


def _place_task(
    task: TaskSnapshot,
    slots: list[FreeSlot],
    now: datetime,
) -> tuple[datetime, datetime, float, list[int]] | None:
    """Find the best consecutive run of free slots for a task."""
    needed = max(task.estimated_minutes, 1)
    best: tuple[float, list[int]] | None = None

    for start_idx in range(len(slots)):
        if slots[start_idx].used:
            continue
        if task.earliest_start and slots[start_idx].start < task.earliest_start:
            continue

        run_indices: list[int] = []
        accumulated = 0
        for idx in range(start_idx, len(slots)):
            if slots[idx].used:
                break
            run_indices.append(idx)
            accumulated += int((slots[idx].end - slots[idx].start).total_seconds() / 60)
            if accumulated >= needed:
                break
        else:
            continue

        if accumulated < needed:
            continue

        end_time = slots[run_indices[-1]].end
        if task.due_date and end_time > task.due_date:
            continue

        avg_energy = sum(slots[i].predicted_energy for i in run_indices) / len(run_indices)
        fit = energy_fit(task.energy_required, avg_energy)
        if best is None or fit > best[0]:
            best = (fit, run_indices)

    if best is None:
        return None

    fit, indices = best
    start = slots[indices[0]].start
    end = slots[indices[0]].start + timedelta(minutes=needed)
    return start, end, fit, indices


def _rationale(task: TaskSnapshot, energy_fit_score: float, now: datetime) -> str:
    parts: list[str] = []
    if task.due_date:
        hours = (task.due_date - now).total_seconds() / 3600
        parts.append(f"due in {hours:.0f}h")
    parts.append(f"energy fit {energy_fit_score:.0%}")
    if task.is_deep_work:
        parts.append("deep work")
    return ", ".join(parts)


def _maybe_insert_break(
    blocks: list[PlannedBlock],
    slots: list[FreeSlot],
    task: TaskSnapshot,
    break_minutes: int,
) -> None:
    """Reserve a short break slot after deep work (best-effort)."""
    if not blocks:
        return
    last = blocks[-1]
    break_start = last.end
    break_end = break_start + timedelta(minutes=break_minutes)
    for slot in slots:
        if not slot.used and slot.start >= break_start:
            slot.used = True
            break
    blocks.append(
        PlannedBlock(
            task_id=None,
            title="Break",
            start=break_start,
            end=break_end,
            kind=TimeBlockKind.BREAK,
            rationale=f"break after {task.title}",
            energy_fit=1.0,
            status=TimeBlockStatus.PROPOSED,
        )
    )
