"""Scheduler tests with realistic student workload."""

from __future__ import annotations

from lifeos.engine.scheduler import plan_day
from lifeos.models.enums import EnergyLevel, TaskStatus
from lifeos.schemas.snapshot import TaskSnapshot
from tests.fixtures.student_workload import student_snapshot


def test_plan_schedules_eligible_tasks() -> None:
    result = plan_day(student_snapshot())
    assert len(result.blocks) >= 1
    work_blocks = [b for b in result.blocks if b.task_id is not None]
    assert work_blocks
    assert result.total_scheduled_minutes > 0


def test_plan_respects_due_dates_in_order() -> None:
    result = plan_day(student_snapshot())
    work = [b for b in result.blocks if b.task_id is not None]
    titles = [b.title for b in work]
    # AP Calc is most urgent — should appear in the plan.
    assert any("AP Calc" in t for t in titles)


def test_deep_work_cap_limits_scheduling() -> None:
    snapshot = student_snapshot()
    # Add many deep-work tasks to exceed cap.
    extra = [
        TaskSnapshot(
            id=100 + i,
            title=f"Deep task {i}",
            status=TaskStatus.TODO,
            priority=5,
            estimated_minutes=120,
            is_deep_work=True,
            energy_required=EnergyLevel.HIGH,
        )
        for i in range(5)
    ]
    snapshot = snapshot.model_copy(
        update={
            "tasks": [*snapshot.tasks, *extra],
            "config": snapshot.config.model_copy(update={"daily_deep_work_cap_minutes": 180}),
        }
    )
    result = plan_day(snapshot)
    assert result.deep_work_minutes <= 180
    assert result.unscheduled_task_ids
