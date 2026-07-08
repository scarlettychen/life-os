"""Project repository."""

from __future__ import annotations

from lifeos.models.enums import ProjectStatus
from lifeos.models.project import Project
from lifeos.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    model = Project

    def list_by_status(self, status: ProjectStatus, *, limit: int = 100) -> list[Project]:
        return self.list(status=status, limit=limit)

    def list_by_area(self, area_id: int, *, limit: int = 100) -> list[Project]:
        return self.list(area_id=area_id, limit=limit)

    def list_by_goal(self, goal_id: int, *, limit: int = 100) -> list[Project]:
        return self.list(goal_id=goal_id, limit=limit)
