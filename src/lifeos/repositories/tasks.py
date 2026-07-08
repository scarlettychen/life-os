"""Task repository."""

from __future__ import annotations

from lifeos.models.base import utcnow
from lifeos.models.enums import TaskStatus
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
