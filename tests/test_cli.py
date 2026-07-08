"""End-to-end CLI tests against an isolated on-disk database."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from typer.testing import CliRunner

from lifeos.cli import app
from lifeos.config import get_settings
from lifeos.db import reset_engine

runner = CliRunner()


@pytest.fixture
def cli_db(tmp_path, monkeypatch) -> Iterator[None]:
    """Point the CLI at a throwaway SQLite file for the duration of a test."""
    db_file = tmp_path / "cli.db"
    monkeypatch.setenv("LIFEOS_DATABASE_URL", f"sqlite:///{db_file}")
    get_settings.cache_clear()
    reset_engine()
    runner.invoke(app, ["init"])
    yield
    reset_engine()
    get_settings.cache_clear()


def _run(*args: str):
    result = runner.invoke(app, list(args))
    assert result.exit_code == 0, result.output
    return result


def test_init_creates_db(cli_db: None) -> None:
    result = runner.invoke(app, ["area", "list"])
    assert result.exit_code == 0


def test_full_crud_flow(cli_db: None) -> None:
    _run("area", "add", "robotics", "--name", "Robotics", "--target", "0.3")
    out = _run("area", "list").output
    assert "robotics" in out

    _run("goal", "add", "Win State", "--area", "1", "--horizon", "long", "--priority", "5")
    assert "Win State" in _run("goal", "list").output

    _run("project", "add", "Swerve", "--area", "1", "--goal", "1", "--effort", "40")
    assert "Swerve" in _run("project", "list").output

    _run("task", "add", "Finish CAD", "--project", "1", "--estimate", "120",
         "--energy", "high", "--deep")
    assert "Finish CAD" in _run("task", "list").output

    done = _run("task", "done", "1", "--actual", "135").output
    assert "done" in done

    assert "done" in _run("task", "show", "1").output


def test_not_found_exits_nonzero(cli_db: None) -> None:
    result = runner.invoke(app, ["task", "show", "999"])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_invalid_priority_rejected(cli_db: None) -> None:
    result = runner.invoke(app, ["task", "add", "x", "--priority", "9"])
    assert result.exit_code != 0
