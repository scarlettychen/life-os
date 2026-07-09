"""Completion logging and calibration integration."""

from __future__ import annotations

from lifeos.models.area import Area
from lifeos.models.task import Task
from lifeos.repositories import CalibrationRepository, CompletionLogRepository, TaskRepository
from lifeos.services.completion import complete_task


def test_complete_task_logs_and_calibrates(session) -> None:
    area = Area(key="robotics", name="Robotics", target_allocation=0.4)
    session.add(area)
    session.flush()
    session.refresh(area)

    task = TaskRepository(session).create(
        Task(title="CAD module", area_id=area.id, estimated_minutes=100)
    )
    assert task.id is not None

    result = complete_task(session, task.id, actual_minutes=150)
    assert result.task.status.value == "done"
    assert result.observed_ratio == 1.5
    assert result.updated_area_ratio == 1.5

    logs = CompletionLogRepository(session).list(limit=10)
    assert len(logs) == 1
    assert logs[0].actual_minutes == 150

    factor = CalibrationRepository(session).get_for_area(area.id)
    assert factor is not None
    assert factor.ratio == 1.5
    assert factor.sample_count == 1


def test_second_completion_updates_ema(session) -> None:
    area = Area(key="school", name="School")
    session.add(area)
    session.flush()
    session.refresh(area)

    t1 = TaskRepository(session).create(Task(title="A", area_id=area.id, estimated_minutes=100))
    t2 = TaskRepository(session).create(Task(title="B", area_id=area.id, estimated_minutes=100))
    assert t1.id is not None and t2.id is not None

    complete_task(session, t1.id, actual_minutes=150)
    complete_task(session, t2.id, actual_minutes=100)

    factor = CalibrationRepository(session).get_for_area(area.id)
    assert factor is not None
    # EMA between 1.5 and 1.0 with alpha 0.3 → 1.35
    assert abs(factor.ratio - 1.35) < 0.01
    assert factor.sample_count == 2
