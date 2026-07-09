"""CLI tests for --due and vault sync."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from typer.testing import CliRunner

from lifeos.cli import app
from lifeos.config import get_settings
from lifeos.db import reset_engine

runner = CliRunner()
VAULT = Path(__file__).resolve().parent / "fixtures" / "vault"


@pytest.fixture
def cli_db(tmp_path, monkeypatch) -> Iterator[None]:
    db_file = tmp_path / "cli.db"
    monkeypatch.setenv("LIFEOS_DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("LIFEOS_VAULT_PATH", str(VAULT))
    get_settings.cache_clear()
    reset_engine()
    runner.invoke(app, ["init"])
    yield
    reset_engine()
    get_settings.cache_clear()


def test_task_add_with_due(cli_db: None) -> None:
    result = runner.invoke(
        app,
        [
            "task",
            "add",
            "AP Calc set 7",
            "--estimate",
            "90",
            "--due",
            "2026-02-05",
            "--priority",
            "4",
        ],
    )
    assert result.exit_code == 0
    assert "23:59" in result.output


def test_task_add_invalid_due(cli_db: None) -> None:
    result = runner.invoke(app, ["task", "add", "x", "--due", "bad-date"])
    assert result.exit_code == 1
    assert "Invalid --due" in result.output


def test_sync_command(cli_db: None) -> None:
    result = runner.invoke(app, ["sync"])
    assert result.exit_code == 0
    assert "Vault sync complete" in result.output
    assert "tasks=" in result.output
