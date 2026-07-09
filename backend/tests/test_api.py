"""API integration tests."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from lifeos.config import get_settings
from lifeos.db import init_db, reset_engine
from lifeos.main import create_app


@pytest.fixture
def api_client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    db_file = tmp_path / "api.db"
    monkeypatch.setenv("LIFEOS_DATABASE_URL", f"sqlite:///{db_file}")
    get_settings.cache_clear()
    reset_engine()
    init_db()
    yield TestClient(create_app())
    reset_engine()
    get_settings.cache_clear()


def test_health(api_client: TestClient) -> None:
    r = api_client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_now_empty(api_client: TestClient) -> None:
    r = api_client.get("/api/now")
    assert r.status_code == 200
    assert "ranked" in r.json()


def test_task_crud(api_client: TestClient) -> None:
    r = api_client.post("/api/tasks", json={"title": "Test task", "priority": 3})
    assert r.status_code == 201
    task_id = r.json()["id"]

    r = api_client.get(f"/api/tasks/{task_id}")
    assert r.status_code == 200

    r = api_client.post(f"/api/tasks/{task_id}/done", json={"actual_minutes": 30})
    assert r.status_code == 200
    assert r.json()["observed_ratio"] > 0


def test_overload(api_client: TestClient) -> None:
    r = api_client.get("/api/overload")
    assert r.status_code == 200
    data = r.json()
    assert data["severity"] in ("green", "yellow", "red")
