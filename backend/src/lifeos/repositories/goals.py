"""Goal repository."""

from __future__ import annotations

from sqlmodel import select

from lifeos.models.enums import GoalStatus, SourceType
from lifeos.models.goal import Goal
from lifeos.repositories.base import BaseRepository


class GoalRepository(BaseRepository[Goal]):
    model = Goal

    def list_by_status(self, status: GoalStatus, *, limit: int = 100) -> list[Goal]:
        return self.list(status=status, limit=limit)

    def list_by_area(self, area_id: int, *, limit: int = 100) -> list[Goal]:
        return self.list(area_id=area_id, limit=limit)

    def get_by_title(self, title: str) -> Goal | None:
        return self.session.exec(select(Goal).where(Goal.title == title)).first()

    def get_by_source_ref(self, source_ref: str) -> Goal | None:
        rows = self.list(source=SourceType.OBSIDIAN, source_ref=source_ref, limit=1)
        return rows[0] if rows else None

    def upsert_obsidian(self, source_ref: str, data: dict) -> Goal:
        existing = self.get_by_source_ref(source_ref)
        payload = {**data, "source": SourceType.OBSIDIAN, "source_ref": source_ref}
        if existing is not None:
            assert existing.id is not None
            updated = self.update(existing.id, payload)
            assert updated is not None
            return updated
        return self.create(Goal.model_validate(payload))
