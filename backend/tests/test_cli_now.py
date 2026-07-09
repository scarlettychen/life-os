"""CLI integration for ``lifeos now``."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta

import pytest
from typer.testing import CliRunner

from lifeos.cli import app
from lifeos.config import get_settings
from lifeos.db import init_db, reset_engine, session_scope
from lifeos.models.area import Area
from lifeos.models.goal import Goal
from lifeos.models.project import Project
from lifeos.models.task import Task
from lifeos.repositories import (
    AreaRepository,
    GoalRepository,
    ProjectRepository,
    TaskRepository,
)

runner = CliRunner()
NOW = datetime(2026, 2, 4, 18, 0)


@pytest.fixture
def seeded_db(tmp_path, monkeypatch) -> Iterator[None]:
    db_file = tmp_path / "now.db"
    monkeypatch.setenv("LIFEOS_DATABASE_URL", f"sqlite:///{db_file}")
    get_settings.cache_clear()
    reset_engine()
    init_db()

    with session_scope() as session:
        school = AreaRepository(session).create(Area(key="school", name="School"))
        isef_area = AreaRepository(session).create(Area(key="isef", name="ISEF"))
        goal = GoalRepository(session).create(
            Goal(title="ISEF paper", area_id=isef_area.id, priority=5, weight=0.95)
        )
        project = ProjectRepository(session).create(
            Project(title="ISEF Paper", area_id=isef_area.id, goal_id=goal.id, priority=5)
        )
        TaskRepository(session).create(
            Task(
                title="AP Calc set 7",
                area_id=school.id,
                estimated_minutes=90,
                due_date=NOW + timedelta(hours=14),
                priority=4,
            )
        )
        TaskRepository(session).create(
            Task(
                title="ISEF abstract",
                project_id=project.id,
                goal_id=goal.id,
                area_id=isef_area.id,
                estimated_minutes=180,
                due_date=NOW + timedelta(hours=30),
                priority=5,
            )
        )

    yield
    reset_engine()
    get_settings.cache_clear()


def test_now_command_runs(seeded_db: None) -> None:
    result = runner.invoke(app, ["now"])
    assert result.exit_code == 0
    assert "Recommended next" in result.output
    assert "Ranked tasks" in result.output
