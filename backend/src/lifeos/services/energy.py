"""Learn energy profile from completion observations."""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Session

from lifeos.engine.calibration import update_ema_ratio
from lifeos.engine.energy import predicted_energy_default
from lifeos.models.enums import EnergyProfileSource
from lifeos.repositories.energy import EnergyLogRepository, EnergyProfileRepository
from lifeos.schemas.snapshot import EngineConfig

DEFAULT_ENERGY_EMA_ALPHA = 0.25


def record_energy_observation(
    session: Session,
    *,
    energy_level: float,
    observed_at: datetime,
    task_id: int | None = None,
    context: str | None = None,
    alpha: float = DEFAULT_ENERGY_EMA_ALPHA,
) -> None:
    """Log energy and update the profile slot for that time."""
    EnergyLogRepository(session).log_observation(
        energy_level=energy_level,
        timestamp=observed_at,
        task_id=task_id,
        context=context,
    )
    _update_profile_from_observation(session, observed_at, energy_level, alpha=alpha)


def ensure_energy_defaults(session: Session) -> None:
    EnergyProfileRepository(session).seed_defaults_if_empty()


def predicted_energy_for(
    session: Session,
    moment: datetime,
) -> float:
    """DB-learned profile first, then static diurnal fallback."""
    ensure_energy_defaults(session)
    # Python weekday: Mon=0; our slots use Mon=0
    day = moment.weekday()
    hour = moment.hour
    slot = EnergyProfileRepository(session).get_slot(day, hour)
    if slot is not None:
        return slot.predicted_energy
    return predicted_energy_default(moment)


def _update_profile_from_observation(
    session: Session,
    moment: datetime,
    observed: float,
    *,
    alpha: float,
) -> None:
    day = moment.weekday()
    hour = moment.hour
    repo = EnergyProfileRepository(session)
    slot = repo.get_slot(day, hour)
    prior = slot.predicted_energy if slot else predicted_energy_default(moment)
    block_start = hour if hour % 2 == 0 else hour - 1
    block_end = block_start + 2
    updated = update_ema_ratio(prior, observed, alpha=alpha)
    repo.upsert_slot(
        day_of_week=day,
        start_hour=block_start,
        end_hour=min(block_end, 24),
        predicted_energy=updated,
        source=EnergyProfileSource.LEARNED,
    )


def apply_satisfaction_weight_nudge(
    session: Session,
    satisfaction: int,
    *,
    config: EngineConfig | None = None,
) -> dict[str, float]:
    """Conservative weight nudge from weekly satisfaction (1-5).

    Low satisfaction slightly increases balance_boost weight (neglected areas).
    Returns the adjusted weights as a dict (not persisted — applied per-request).
    """
    cfg = config or EngineConfig()
    weights = cfg.weights.model_copy()
    if satisfaction <= 2:
        weights.balance_boost = min(0.15, weights.balance_boost + 0.02)
        weights.urgency = max(0.20, weights.urgency - 0.02)
    elif satisfaction >= 4:
        weights.balance_boost = max(0.05, weights.balance_boost - 0.01)
    return weights.model_dump()
