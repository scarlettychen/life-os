"""CRUD behavior of the repository layer."""

from __future__ import annotations

import pytest
from sqlmodel import Session

from lifeos.models.area import Area
from lifeos.models.enums import GoalStatus, ProjectStatus, TaskStatus
from lifeos.models.goal import Goal
from lifeos.models.project import Project
from lifeos.models.task import Task
from lifeos.repositories import (
    AreaRepository,
    GoalRepository,
    ProjectRepository,
    TaskRepository,
)


def test_area_crud(session: Session) -> None:
    repo = AreaRepository(session)
    area = repo.create(Area(key="robotics", name="Competitive Robotics", target_allocation=0.3))
    assert area.id is not None
    assert area.created_at is not None

    fetched = repo.get(area.id)
    assert fetched is not None
    assert fetched.name == "Competitive Robotics"

    assert repo.get_by_key("robotics") is not None
    assert repo.get_by_key("missing") is None

    updated = repo.update(area.id, {"name": "Robotics"})
    assert updated is not None
    assert updated.name == "Robotics"
    assert updated.updated_at >= updated.created_at

    assert repo.delete(area.id) is True
    assert repo.get(area.id) is None
    assert repo.delete(area.id) is False


def test_goal_crud_and_filters(session: Session) -> None:
    area = AreaRepository(session).create(Area(key="isef", name="ISEF"))
    repo = GoalRepository(session)

    active = repo.create(Goal(title="Publish paper", area_id=area.id, priority=5))
    repo.create(Goal(title="Old goal", area_id=area.id, status=GoalStatus.DROPPED))

    assert repo.get(active.id).priority == 5
    assert len(repo.list()) == 2
    assert len(repo.list_by_status(GoalStatus.ACTIVE)) == 1
    assert len(repo.list_by_area(area.id)) == 2

    moved = repo.update(active.id, {"status": GoalStatus.DONE, "progress": 1.0})
    assert moved.status is GoalStatus.DONE
    assert moved.progress == 1.0


def test_project_crud(session: Session) -> None:
    repo = ProjectRepository(session)
    project = repo.create(Project(title="Swerve Drivetrain", estimated_effort_hours=40))
    assert project.id is not None
    assert project.status is ProjectStatus.PLANNED

    updated = repo.update(project.id, {"status": ProjectStatus.ACTIVE, "progress": 0.25})
    assert updated.status is ProjectStatus.ACTIVE
    assert updated.progress == 0.25

    assert len(repo.list_by_status(ProjectStatus.ACTIVE)) == 1


def test_task_crud_and_mark_done(session: Session) -> None:
    project = ProjectRepository(session).create(Project(title="Drivetrain"))
    repo = TaskRepository(session)

    task = repo.create(
        Task(title="Finish CAD", project_id=project.id, estimated_minutes=120, priority=4)
    )
    assert task.status is TaskStatus.TODO
    assert task.completed_at is None

    open_task = repo.create(Task(title="Order bearings", project_id=project.id))
    assert len(repo.list_open()) == 2
    assert len(repo.list_by_project(project.id)) == 2

    done = repo.mark_done(task.id, actual_minutes=135)
    assert done is not None
    assert done.status is TaskStatus.DONE
    assert done.completed_at is not None
    assert done.actual_minutes == 135

    assert len(repo.list_open()) == 1
    assert len(repo.list_by_status(TaskStatus.DONE)) == 1
    # untouched task remains open
    assert repo.get(open_task.id).status is TaskStatus.TODO


def test_update_missing_returns_none(session: Session) -> None:
    repo = TaskRepository(session)
    assert repo.update(999, {"title": "nope"}) is None
    assert repo.mark_done(999) is None


def test_transaction_rolls_back_on_error(engine) -> None:
    """A failed unit of work should not persist partial writes."""
    from lifeos.db import session_scope

    with pytest.raises(RuntimeError):  # noqa: SIM117
        with session_scope(engine) as session:
            AreaRepository(session).create(Area(key="temp", name="Temp"))
            raise RuntimeError("boom")

    with session_scope(engine) as session:
        assert AreaRepository(session).get_by_key("temp") is None
