"""Default energy profile — predicted energy by time of day."""

from __future__ import annotations

from datetime import datetime

from lifeos.models.enums import EnergyLevel


def energy_level_to_score(level: EnergyLevel) -> float:
    """Map task energy requirement to a 0-1 scale."""
    return {
        EnergyLevel.LOW: 0.3,
        EnergyLevel.MEDIUM: 0.6,
        EnergyLevel.HIGH: 0.9,
    }[level]


def predicted_energy_at(moment: datetime) -> float:
    """Return predicted personal energy (0-1) for a given clock time.

    Static diurnal curve — use ``predicted_energy_for(session, moment)`` when a
    DB session is available for learned profiles.
    """
    return predicted_energy_default(moment)


def predicted_energy_default(moment: datetime) -> float:
    hour = moment.hour + moment.minute / 60.0
    if hour < 7 or hour >= 22:
        return 0.15
    if hour < 12:
        return 0.85
    if hour < 17:
        return 0.60
    return 0.35


def energy_fit(task_energy: EnergyLevel, slot_energy: float) -> float:
    """How well a task's energy requirement matches a slot (0-1, higher is better)."""
    required = energy_level_to_score(task_energy)
    return max(0.0, 1.0 - abs(required - slot_energy))
