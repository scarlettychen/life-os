"""Goal repository."""

from __future__ import annotations

from lifeos.models.enums import GoalStatus
from lifeos.models.goal import Goal
from lifeos.repositories.base import BaseRepository


class GoalRepository(BaseRepository[Goal]):
    model = Goal

    def list_by_status(self, status: GoalStatus, *, limit: int = 100) -> list[Goal]:
        return self.list(status=status, limit=limit)

    def list_by_area(self, area_id: int, *, limit: int = 100) -> list[Goal]:
        return self.list(area_id=area_id, limit=limit)
