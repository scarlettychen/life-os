"""CLI tests for plan, rest, and brief."""

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


def test_plan_command(cli_db: None) -> None:
    result = runner.invoke(app, ["plan"])
    assert result.exit_code == 0


def test_rest_command(cli_db: None) -> None:
    result = runner.invoke(app, ["rest", "--hours", "2"])
    assert result.exit_code == 0
    assert "Rest verdict" in result.output


def test_brief_dry_run(cli_db: None) -> None:
    result = runner.invoke(app, ["brief", "--dry-run"])
    assert result.exit_code == 0
    assert "Today's Plan" in result.output
