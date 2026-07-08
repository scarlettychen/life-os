"""Data-access layer. All database queries live in repositories."""

from lifeos.repositories.areas import AreaRepository
from lifeos.repositories.base import BaseRepository
from lifeos.repositories.goals import GoalRepository
from lifeos.repositories.projects import ProjectRepository
from lifeos.repositories.tasks import TaskRepository

__all__ = [
    "BaseRepository",
    "AreaRepository",
    "GoalRepository",
    "ProjectRepository",
    "TaskRepository",
]
