"""CalibrationFactor repository."""

from __future__ import annotations

from sqlmodel import select

from lifeos.models.base import utcnow
from lifeos.models.calibration import CalibrationFactor
from lifeos.repositories.base import BaseRepository


class CalibrationRepository(BaseRepository[CalibrationFactor]):
    model = CalibrationFactor

    def get_for_area(self, area_id: int | None) -> CalibrationFactor | None:
        statement = select(CalibrationFactor).where(CalibrationFactor.area_id == area_id)
        return self.session.exec(statement).first()

    def get_or_create(self, area_id: int | None) -> CalibrationFactor:
        existing = self.get_for_area(area_id)
        if existing is not None:
            return existing
        return self.create(CalibrationFactor(area_id=area_id))

    def list_all(self, *, limit: int = 100) -> list[CalibrationFactor]:
        return self.list(limit=limit)

    def save_ratio(
        self,
        area_id: int | None,
        *,
        ratio: float,
        increment_samples: int = 1,
    ) -> CalibrationFactor:
        factor = self.get_or_create(area_id)
        factor.ratio = ratio
        factor.sample_count += increment_samples
        factor.updated_at = utcnow()
        self.session.add(factor)
        self.session.flush()
        self.session.refresh(factor)
        return factor
