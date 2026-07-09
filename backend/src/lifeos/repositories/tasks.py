"""Task repository."""

from __future__ import annotations

from lifeos.models.base import utcnow
from lifeos.models.enums import SourceType, TaskStatus
from lifeos.models.task import Task
from lifeos.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    model = Task

    def list_by_status(self, status: TaskStatus, *, limit: int = 100) -> list[Task]:
        return self.list(status=status, limit=limit)

    def list_by_project(self, project_id: int, *, limit: int = 100) -> list[Task]:
        return self.list(project_id=project_id, limit=limit)

    def list_open(self, *, limit: int = 100) -> list[Task]:
        """Tasks that are neither done nor dropped."""
        return [
            t
            for t in self.list(limit=limit)
            if t.status not in (TaskStatus.DONE, TaskStatus.DROPPED)
        ]

    def mark_done(self, task_id: int, *, actual_minutes: int | None = None) -> Task | None:
        """Mark a task complete, stamping the completion time."""
        task = self.get(task_id)
        if task is None:
            return None
        task.status = TaskStatus.DONE
        task.completed_at = utcnow()
        if actual_minutes is not None:
            task.actual_minutes = actual_minutes
        task.updated_at = utcnow()
        self.session.add(task)
        self.session.flush()
        self.session.refresh(task)
        return task

    def get_by_source_ref(self, source_ref: str) -> Task | None:
        rows = self.list(source=SourceType.OBSIDIAN, source_ref=source_ref, limit=1)
        return rows[0] if rows else None

    def list_obsidian(self, *, limit: int = 2000) -> list[Task]:
        return self.list(source=SourceType.OBSIDIAN, limit=limit)

    def upsert_obsidian(self, source_ref: str, data: dict) -> Task:
        existing = self.get_by_source_ref(source_ref)
        payload = {**data, "source": SourceType.OBSIDIAN, "source_ref": source_ref}
        if existing is not None:
            assert existing.id is not None
            updated = self.update(existing.id, payload)
            assert updated is not None
            return updated
        return self.create(Task.model_validate(payload))

    def mark_missing_obsidian_dropped(self, seen_refs: set[str]) -> int:
        """Soft-delete Obsidian tasks no longer present in the vault."""
        dropped = 0
        for task in self.list_obsidian():
            if (
                task.source_ref
                and task.source_ref not in seen_refs
                and task.status not in (TaskStatus.DONE, TaskStatus.DROPPED)
            ):
                assert task.id is not None
                self.update(task.id, {"status": TaskStatus.DROPPED})
                dropped += 1
        return dropped
