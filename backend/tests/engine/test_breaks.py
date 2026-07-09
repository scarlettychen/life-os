"""Rest feasibility tests."""

from __future__ import annotations

from datetime import timedelta

from lifeos.engine.breaks import evaluate_rest
from lifeos.models.enums import RestVerdict, TaskStatus
from lifeos.schemas.snapshot import TaskSnapshot
from tests.fixtures.student_workload import NOW, student_snapshot


def test_can_rest_when_schedule_is_loose() -> None:
    snapshot = student_snapshot()
    result = evaluate_rest(snapshot, hours=2)
    assert result.verdict is RestVerdict.YES


def test_cannot_rest_all_day_when_deadline_tight() -> None:
    snapshot = student_snapshot()
    tight = TaskSnapshot(
        id=99,
        title="Emergency lab report",
        status=TaskStatus.TODO,
        priority=5,
        estimated_minutes=240,
        due_date=NOW + timedelta(hours=3),
        is_hard_deadline=True,
    )
    snapshot = snapshot.model_copy(update={"tasks": [*snapshot.tasks, tight]})
    result = evaluate_rest(snapshot, hours=8)
    assert result.verdict in (RestVerdict.NO, RestVerdict.PARTIAL)
    assert result.minimum_work_minutes > 0
