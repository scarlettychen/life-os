"""Area repository."""

from __future__ import annotations

from sqlmodel import select

from lifeos.models.area import Area
from lifeos.repositories.base import BaseRepository


class AreaRepository(BaseRepository[Area]):
    model = Area

    def get_by_key(self, key: str) -> Area | None:
        return self.session.exec(select(Area).where(Area.key == key)).first()

    def upsert_obsidian(self, source_ref: str, data: dict) -> Area:
        """Upsert an area keyed by ``key`` (areas are not source-tracked in M2)."""
        _ = source_ref
        existing = self.get_by_key(data["key"])
        if existing is not None:
            assert existing.id is not None
            updated = self.update(existing.id, data)
            assert updated is not None
            return updated
        return self.create(Area.model_validate(data))
