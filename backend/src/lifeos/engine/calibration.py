"""Estimation calibration — EMA of actual/estimated ratios."""

from __future__ import annotations

DEFAULT_EMA_ALPHA = 0.3
MIN_RATIO = 0.25
MAX_RATIO = 4.0


def update_ema_ratio(
    current: float | None,
    observed_ratio: float,
    *,
    alpha: float = DEFAULT_EMA_ALPHA,
) -> float:
    """Exponential moving average for actual/estimated ratio."""
    clamped = max(MIN_RATIO, min(MAX_RATIO, observed_ratio))
    if current is None:
        return clamped
    return alpha * clamped + (1.0 - alpha) * current


def adjust_estimate(raw_minutes: int, ratio: float) -> int:
    """Apply a calibration ratio to a raw estimate."""
    safe_ratio = max(MIN_RATIO, min(MAX_RATIO, ratio))
    return max(15, int(round(raw_minutes * safe_ratio)))


def resolve_ratio(
    area_id: int | None,
    *,
    area_ratios: dict[int, float],
    global_ratio: float = 1.0,
) -> float:
    """Area-specific ratio, else global fallback."""
    if area_id is not None and area_id in area_ratios:
        return area_ratios[area_id]
    return global_ratio
