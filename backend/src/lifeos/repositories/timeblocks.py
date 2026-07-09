"""TimeBlock repository."""

from __future__ import annotations

from datetime import datetime

from sqlmodel import select

from lifeos.models.enums import TimeBlockStatus
from lifeos.models.timeblock import TimeBlock
from lifeos.repositories.base import BaseRepository


class TimeBlockRepository(BaseRepository[TimeBlock]):
    model = TimeBlock

    def list_for_day(self, day_start: datetime, day_end: datetime) -> list[TimeBlock]:
        statement = (
            select(TimeBlock)
            .where(TimeBlock.start >= day_start)
            .where(TimeBlock.start < day_end)
            .order_by(TimeBlock.start)  # type: ignore[arg-type]
        )
        return list(self.session.exec(statement).all())

    def replace_proposed_for_day(
        self,
        day_start: datetime,
        day_end: datetime,
        blocks: list[TimeBlock],
    ) -> list[TimeBlock]:
        """Remove existing proposed blocks for the day and store new ones."""
        existing = self.list_for_day(day_start, day_end)
        for block in existing:
            if block.status is TimeBlockStatus.PROPOSED and block.id is not None:
                self.delete(block.id)
        saved: list[TimeBlock] = []
        for block in blocks:
            saved.append(self.create(block))
        return saved
