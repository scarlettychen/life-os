"""Scheduling conflict detection tests."""

from __future__ import annotations

from lifeos.engine.conflicts import detect_conflicts
from lifeos.schemas.results import ConflictKind
from tests.fixtures.student_workload import conflict_snapshot, student_snapshot


def test_no_conflicts_on_normal_student_week() -> None:
    snapshot = student_snapshot()
    conflicts = detect_conflicts(snapshot)
    assert conflicts == []


def test_detects_infeasible_deadline() -> None:
    snapshot = conflict_snapshot()
    conflicts = detect_conflicts(snapshot)
    kinds = {c.kind for c in conflicts}
    assert ConflictKind.INFEASIBLE_DEADLINE in kinds

    physics = next(c for c in conflicts if c.kind is ConflictKind.INFEASIBLE_DEADLINE)
    assert 10 in physics.task_ids
    assert "Physics lab report" in physics.message


def test_detects_same_day_overload() -> None:
    snapshot = conflict_snapshot()
    conflicts = detect_conflicts(snapshot)
    overloads = [c for c in conflicts if c.kind is ConflictKind.DAY_OVERLOAD]
    assert len(overloads) >= 1

    friday = next(c for c in overloads if c.due_date == "2026-02-06")
    # ISEF abstract (base) + three Friday tasks = 180 + 120 + 90 + 90 = 480 min.
    assert friday.demand_minutes == 480
    assert friday.capacity_minutes == 240
    assert {1, 11, 12, 13}.issubset(set(friday.task_ids))
