"""Project repository."""

from __future__ import annotations

from lifeos.models.enums import ProjectStatus, SourceType
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

    def get_by_source_ref(self, source_ref: str) -> Project | None:
        rows = self.list(source=SourceType.OBSIDIAN, source_ref=source_ref, limit=1)
        return rows[0] if rows else None

    def upsert_obsidian(self, source_ref: str, data: dict) -> Project:
        existing = self.get_by_source_ref(source_ref)
        payload = {**data, "source": SourceType.OBSIDIAN, "source_ref": source_ref}
        if existing is not None:
            assert existing.id is not None
            updated = self.update(existing.id, payload)
            assert updated is not None
            return updated
        return self.create(Project.model_validate(payload))
