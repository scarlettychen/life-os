"""Overload severity report and cut-list suggestions."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from lifeos.engine.conflicts import detect_conflicts
from lifeos.engine.recommend import rank_tasks
from lifeos.engine.scoring import is_eligible
from lifeos.schemas.results import ConflictKind, RankedTask, ScheduleConflict
from lifeos.schemas.snapshot import EngineSnapshot, TaskSnapshot


class OverloadSeverity(StrEnum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class OverloadReport(BaseModel):
    severity: OverloadSeverity
    label: str
    conflicts: list[ScheduleConflict]
    cut_list: list[RankedTask] = Field(default_factory=list)
    eligible_count: int = 0


def assess_overload(snapshot: EngineSnapshot) -> OverloadReport:
    """Compute workload severity and suggest low-priority tasks to cut."""
    eligible = [t for t in snapshot.tasks if is_eligible(t, now=snapshot.now)]
    conflicts = detect_conflicts(snapshot, tasks=eligible)
    ranked = rank_tasks(snapshot)

    has_infeasible = any(c.kind is ConflictKind.INFEASIBLE_DEADLINE for c in conflicts)
    if has_infeasible:
        severity = OverloadSeverity.RED
    elif conflicts:
        severity = OverloadSeverity.YELLOW
    else:
        severity = OverloadSeverity.GREEN

    task_by_id = {t.id: t for t in snapshot.tasks}
    cut_list = _suggest_cut_list(ranked, task_by_id)

    from lifeos.engine.explain import overload_label

    return OverloadReport(
        severity=severity,
        label=overload_label(severity.value),
        conflicts=conflicts,
        cut_list=cut_list,
        eligible_count=len(eligible),
    )


def _suggest_cut_list(
    ranked: list[RankedTask],
    tasks: dict[int, TaskSnapshot],
    *,
    limit: int = 5,
) -> list[RankedTask]:
    """Lowest-ranked non-critical tasks — candidates to drop or defer."""
    if not ranked:
        return []
    cuts: list[RankedTask] = []
    for item in reversed(ranked):
        task = tasks.get(item.task_id)
        if task is None:
            continue
        if task.is_hard_deadline:
            continue
        if task.pinned:
            continue
        cuts.append(item)
        if len(cuts) >= limit:
            break
    return cuts
