"""Weekly review generation."""

from __future__ import annotations

from datetime import date, datetime

from lifeos.models.area import Area
from lifeos.models.task import Task
from lifeos.repositories import TaskRepository
from lifeos.services.completion import complete_task
from lifeos.services.review import generate_review_markdown, week_start_for


def test_week_start_is_monday() -> None:
    assert week_start_for(date(2026, 2, 4)) == date(2026, 2, 2)


def test_generate_review_includes_completions(session) -> None:
    area = Area(key="isef", name="ISEF", target_allocation=0.5)
    session.add(area)
    session.flush()
    session.refresh(area)

    task = TaskRepository(session).create(
        Task(title="Abstract draft", area_id=area.id, estimated_minutes=60)
    )
    assert task.id is not None
    complete_task(
        session,
        task.id,
        actual_minutes=90,
        completed_at=datetime(2026, 2, 4, 15, 0),
    )

    week = week_start_for(date(2026, 2, 4))
    body, record = generate_review_markdown(session, week_start=week)
    assert "Abstract draft" in body
    assert "Completed tasks" in body
    assert record.planned_vs_actual["actual_minutes"] == 90
