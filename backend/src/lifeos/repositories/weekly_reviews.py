"""WeeklyReview repository."""

from __future__ import annotations

from datetime import date

from sqlmodel import select

from lifeos.models.base import utcnow
from lifeos.models.weekly_review import WeeklyReview, WeeklyReviewCreate
from lifeos.repositories.base import BaseRepository


class WeeklyReviewRepository(BaseRepository[WeeklyReview]):
    model = WeeklyReview

    def get_by_week(self, week_start: date) -> WeeklyReview | None:
        statement = select(WeeklyReview).where(WeeklyReview.week_start == week_start)
        return self.session.exec(statement).first()

    def upsert(self, data: WeeklyReviewCreate) -> WeeklyReview:
        existing = self.get_by_week(data.week_start)
        if existing is None:
            return self.create(WeeklyReview.model_validate(data))

        payload = data.model_dump()
        for field, value in payload.items():
            setattr(existing, field, value)
        existing.updated_at = utcnow()
        self.session.add(existing)
        self.session.flush()
        self.session.refresh(existing)
        return existing
