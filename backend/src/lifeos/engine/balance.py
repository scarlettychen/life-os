"""Goal-balance drift from completion history."""

from __future__ import annotations

from lifeos.schemas.snapshot import CompletionLogSnapshot


def compute_actual_allocations(
    logs: list[CompletionLogSnapshot],
) -> dict[int, float]:
    """Share of completed minutes per area over the trailing window."""
    totals: dict[int, int] = {}
    for log in logs:
        if log.area_id is None:
            continue
        totals[log.area_id] = totals.get(log.area_id, 0) + log.actual_minutes

    grand_total = sum(totals.values())
    if grand_total <= 0:
        return {}
    return {area_id: minutes / grand_total for area_id, minutes in totals.items()}


def compute_balance_drift(
    *,
    target_allocations: dict[int, float],
    actual_allocations: dict[int, float],
) -> dict[int, float]:
    """Positive drift means the area is underserved (target > actual)."""
    drift: dict[int, float] = {}
    for area_id, target in target_allocations.items():
        actual = actual_allocations.get(area_id, 0.0)
        drift[area_id] = target - actual
    return drift


def compute_balance_boost(
    area_id: int | None,
    drift: dict[int, float],
    *,
    gain: float = 1.0,
    cap: float = 0.15,
) -> float:
    """Soft ranking nudge for underserved areas."""
    if area_id is None:
        return 0.0
    value = drift.get(area_id, 0.0)
    if value <= 0:
        return 0.0
    return min(cap, gain * value)
