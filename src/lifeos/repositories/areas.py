"""Area repository."""

from __future__ import annotations

from sqlmodel import select

from lifeos.models.area import Area
from lifeos.repositories.base import BaseRepository


class AreaRepository(BaseRepository[Area]):
    model = Area

    def get_by_key(self, key: str) -> Area | None:
        return self.session.exec(select(Area).where(Area.key == key)).first()
