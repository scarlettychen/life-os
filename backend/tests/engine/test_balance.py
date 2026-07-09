"""Unit tests for balance drift and ranking boost."""

from __future__ import annotations

from datetime import datetime

from lifeos.engine.balance import (
    compute_actual_allocations,
    compute_balance_boost,
    compute_balance_drift,
)
from lifeos.schemas.snapshot import CompletionLogSnapshot


def _log(area_id: int, minutes: int) -> CompletionLogSnapshot:
    return CompletionLogSnapshot(
        task_id=1,
        area_id=area_id,
        estimated_minutes=minutes,
        actual_minutes=minutes,
        completed_at=datetime(2026, 2, 4, 12, 0),
    )


def test_actual_allocations_from_completions() -> None:
    logs = [_log(1, 60), _log(1, 60), _log(2, 120)]
    actual = compute_actual_allocations(logs)
    assert actual[1] == 0.5
    assert actual[2] == 0.5


def test_balance_drift_positive_when_underserved() -> None:
    drift = compute_balance_drift(
        target_allocations={1: 0.6, 2: 0.4},
        actual_allocations={1: 0.2, 2: 0.8},
    )
    assert drift[1] > 0
    assert drift[2] < 0


def test_balance_boost_only_for_positive_drift() -> None:
    drift = {1: 0.2, 2: -0.1}
    assert compute_balance_boost(1, drift) > 0
    assert compute_balance_boost(2, drift) == 0.0
