"""Unit tests for estimation calibration."""

from __future__ import annotations

from lifeos.engine.calibration import adjust_estimate, resolve_ratio, update_ema_ratio


def test_ema_first_observation() -> None:
    assert update_ema_ratio(None, 1.4) == 1.4


def test_ema_blends_toward_new_observation() -> None:
    result = update_ema_ratio(1.0, 2.0, alpha=0.5)
    assert result == 1.5


def test_adjust_estimate_scales_up() -> None:
    assert adjust_estimate(100, 1.4) == 140


def test_resolve_ratio_prefers_area() -> None:
    assert resolve_ratio(2, area_ratios={2: 1.3}, global_ratio=1.0) == 1.3
    assert resolve_ratio(9, area_ratios={2: 1.3}, global_ratio=1.1) == 1.1
