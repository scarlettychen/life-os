"""Energy profile and log repositories."""

from __future__ import annotations

from datetime import datetime

from sqlmodel import col, select

from lifeos.models.base import utcnow
from lifeos.models.energy import EnergyLog, EnergyProfileSlot
from lifeos.models.enums import EnergyProfileSource
from lifeos.repositories.base import BaseRepository


class EnergyProfileRepository(BaseRepository[EnergyProfileSlot]):
    model = EnergyProfileSlot

    def get_slot(self, day_of_week: int, hour: int) -> EnergyProfileSlot | None:
        statement = select(EnergyProfileSlot).where(
            EnergyProfileSlot.day_of_week == day_of_week,
            EnergyProfileSlot.start_hour <= hour,
            EnergyProfileSlot.end_hour > hour,
        )
        return self.session.exec(statement).first()

    def upsert_slot(
        self,
        *,
        day_of_week: int,
        start_hour: int,
        end_hour: int,
        predicted_energy: float,
        source: EnergyProfileSource = EnergyProfileSource.LEARNED,
    ) -> EnergyProfileSlot:
        statement = select(EnergyProfileSlot).where(
            EnergyProfileSlot.day_of_week == day_of_week,
            EnergyProfileSlot.start_hour == start_hour,
            EnergyProfileSlot.end_hour == end_hour,
        )
        existing = self.session.exec(statement).first()
        if existing is not None:
            existing.predicted_energy = predicted_energy
            existing.source = source
            existing.updated_at = utcnow()
            self.session.add(existing)
            self.session.flush()
            self.session.refresh(existing)
            return existing
        return self.create(
            EnergyProfileSlot(
                day_of_week=day_of_week,
                start_hour=start_hour,
                end_hour=end_hour,
                predicted_energy=predicted_energy,
                source=source,
            )
        )

    def seed_defaults_if_empty(self) -> None:
        if self.list(limit=1):
            return
        defaults = [
            (0, 22, 0.15),
            (7, 12, 0.85),
            (12, 17, 0.60),
            (17, 22, 0.35),
        ]
        for start, end, energy in defaults:
            for day in range(7):
                self.create(
                    EnergyProfileSlot(
                        day_of_week=day,
                        start_hour=start,
                        end_hour=end,
                        predicted_energy=energy,
                        source=EnergyProfileSource.DEFAULT,
                    )
                )


class EnergyLogRepository(BaseRepository[EnergyLog]):
    model = EnergyLog

    def log_observation(
        self,
        *,
        energy_level: float,
        timestamp: datetime | None = None,
        task_id: int | None = None,
        context: str | None = None,
        note: str | None = None,
    ) -> EnergyLog:
        return self.create(
            EnergyLog(
                timestamp=timestamp or utcnow(),
                energy_level=energy_level,
                task_id=task_id,
                context=context,
                note=note,
            )
        )

    def list_since(self, since: datetime, *, limit: int = 500) -> list[EnergyLog]:
        statement = (
            select(EnergyLog)
            .where(EnergyLog.timestamp >= since)
            .order_by(col(EnergyLog.timestamp).desc())
            .limit(limit)
        )
        return list(self.session.exec(statement).all())
