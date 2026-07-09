"""Build free time slots for scheduling."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from lifeos.engine.energy import predicted_energy_at
from lifeos.schemas.snapshot import EngineConfig


@dataclass
class FreeSlot:
    start: datetime
    end: datetime
    predicted_energy: float
    used: bool = False


def build_free_slots(
    *,
    now: datetime,
    horizon_end: datetime,
    config: EngineConfig,
) -> list[FreeSlot]:
    """Create discrete free slots from ``now`` until ``horizon_end``."""
    slot_delta = timedelta(minutes=config.slot_minutes)
    slots: list[FreeSlot] = []

    cursor = now
    if cursor.minute % config.slot_minutes:
        # Align to next slot boundary.
        remainder = config.slot_minutes - (cursor.minute % config.slot_minutes)
        cursor = cursor.replace(second=0, microsecond=0) + timedelta(minutes=remainder)

    while cursor < horizon_end:
        if not _is_within_waking_hours(cursor, config):
            cursor += slot_delta
            continue
        end = cursor + slot_delta
        if end > horizon_end:
            break
        slots.append(
            FreeSlot(
                start=cursor,
                end=end,
                predicted_energy=predicted_energy_at(cursor),
            )
        )
        cursor = end

    return slots


def day_horizon_end(now: datetime, config: EngineConfig) -> datetime:
    """End of the scheduling horizon for today (``day_end_hour``)."""
    end = now.replace(hour=config.day_end_hour, minute=0, second=0, microsecond=0)
    if end <= now:
        end += timedelta(days=1)
    return end


def _is_within_waking_hours(moment: datetime, config: EngineConfig) -> bool:
    return config.day_start_hour <= moment.hour < config.day_end_hour
