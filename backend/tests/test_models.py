"""Validation and default behavior of the data models.

Note: SQLModel *table* models skip validation, so constraints are enforced on
the ``*Create`` schemas. These tests target those schemas.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from lifeos.models.area import AreaCreate
from lifeos.models.enums import EnergyLevel, GoalHorizon, TaskStatus
from lifeos.models.goal import GoalCreate
from lifeos.models.task import TaskCreate


def test_task_defaults() -> None:
    task = TaskCreate(title="Write abstract")
    assert task.status is TaskStatus.TODO
    assert task.priority == 3
    assert task.energy_required is EnergyLevel.MEDIUM
    assert task.is_deep_work is False


def test_goal_defaults() -> None:
    goal = GoalCreate(title="Win state")
    assert goal.horizon is GoalHorizon.MEDIUM
    assert goal.progress == 0.0


@pytest.mark.parametrize("priority", [0, 6, -1])
def test_priority_out_of_range_rejected(priority: int) -> None:
    with pytest.raises(ValidationError):
        TaskCreate(title="x", priority=priority)


def test_progress_out_of_range_rejected() -> None:
    with pytest.raises(ValidationError):
        GoalCreate(title="x", progress=1.5)


def test_area_target_allocation_bounds() -> None:
    with pytest.raises(ValidationError):
        AreaCreate(key="x", name="X", target_allocation=1.5)


def test_negative_estimate_rejected() -> None:
    with pytest.raises(ValidationError):
        TaskCreate(title="x", estimated_minutes=-10)
