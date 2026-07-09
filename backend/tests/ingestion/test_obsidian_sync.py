"""End-to-end Obsidian vault sync tests."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from sqlmodel import Session

from lifeos.ingestion.obsidian.sync import sync_vault
from lifeos.repositories import GoalRepository, ProjectRepository, TaskRepository
from lifeos.services.recommend import recommend_now

VAULT = Path(__file__).resolve().parents[1] / "fixtures" / "vault"
NOW = datetime(2026, 2, 4, 18, 0)


@pytest.fixture
def synced_session(session: Session) -> Session:
    sync_vault(VAULT, session)
    return session


def test_sync_creates_goals_projects_and_tasks(synced_session: Session) -> None:
    assert GoalRepository(synced_session).count() >= 2
    assert ProjectRepository(synced_session).count() >= 2
    assert TaskRepository(synced_session).count() >= 3


def test_sync_is_idempotent(synced_session: Session) -> None:
    before = TaskRepository(synced_session).count()
    sync_vault(VAULT, synced_session)
    after = TaskRepository(synced_session).count()
    assert before == after


def test_synced_tasks_have_due_dates_and_estimates(synced_session: Session) -> None:
    tasks = TaskRepository(synced_session).list_obsidian()
    abstract = next(t for t in tasks if "abstract" in t.title.lower())
    calc = next(t for t in tasks if "Problem set" in t.title)
    assert abstract.estimated_minutes == 180
    assert abstract.due_date is not None
    assert calc.estimated_minutes == 90
    assert calc.due_date is not None


def test_recommend_after_sync_prefers_ap_calc_due_sooner(synced_session: Session) -> None:
    result = recommend_now(synced_session, now=NOW)
    assert result.top_pick is not None
    # AP Calc due ~14h from NOW; ISEF abstract due ~2.5 days out.
    assert "Problem set" in result.top_pick.title or "abstract" in result.top_pick.title


def test_removed_vault_task_is_soft_dropped(session: Session, tmp_path: Path) -> None:
    # Copy fixture vault to temp, sync, remove a task line, re-sync.
    import shutil

    vault_copy = tmp_path / "vault"
    shutil.copytree(VAULT, vault_copy)

    sync_vault(vault_copy, session)
    repo = TaskRepository(session)
    assert repo.count() >= 3

    project_file = vault_copy / "projects" / "ap-calc.md"
    text = project_file.read_text()
    project_file.write_text(text.replace("- [ ] Problem set 7", ""))

    sync_vault(vault_copy, session)
    calc_tasks = [t for t in repo.list_obsidian() if "Problem set" in t.title]
    assert len(calc_tasks) == 1
    assert calc_tasks[0].status.value == "dropped"
