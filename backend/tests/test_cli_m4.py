"""CLI tests for M4 completion and review commands."""

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
    runner.invoke(app, ["sync"])
    yield
    reset_engine()
    get_settings.cache_clear()


def test_done_command(cli_db: None) -> None:
    result = runner.invoke(
        app,
        ["done", "1", "--actual", "45"],
    )
    assert result.exit_code == 0
    assert "Completed" in result.output
    assert "calibration" in result.output.lower()


def test_calibrate_empty(cli_db: None) -> None:
    result = runner.invoke(app, ["calibrate"])
    assert result.exit_code == 0


def test_review_dry_run(cli_db: None) -> None:
    runner.invoke(app, ["done", "1", "--actual", "30"])
    result = runner.invoke(app, ["review", "--dry-run"])
    assert result.exit_code == 0
    assert "Weekly review" in result.output
