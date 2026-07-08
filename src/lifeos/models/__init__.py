"""SQLModel data models for LifeOS.

Importing this package registers every table on ``SQLModel.metadata`` so that
``init_db`` can create the full schema.
"""

from __future__ import annotations

from lifeos.models.area import Area, AreaCreate, AreaUpdate
from lifeos.models.base import TimestampMixin, utcnow
from lifeos.models.enums import (
    EnergyLevel,
    GoalHorizon,
    GoalStatus,
    ProjectStatus,
    SourceType,
    TaskStatus,
)
from lifeos.models.goal import Goal, GoalCreate, GoalUpdate
from lifeos.models.project import Project, ProjectCreate, ProjectUpdate
from lifeos.models.task import Task, TaskCreate, TaskUpdate

__all__ = [
    # base
    "TimestampMixin",
    "utcnow",
    # enums
    "EnergyLevel",
    "GoalHorizon",
    "GoalStatus",
    "ProjectStatus",
    "SourceType",
    "TaskStatus",
    # area
    "Area",
    "AreaCreate",
    "AreaUpdate",
    # goal
    "Goal",
    "GoalCreate",
    "GoalUpdate",
    # project
    "Project",
    "ProjectCreate",
    "ProjectUpdate",
    # task
    "Task",
    "TaskCreate",
    "TaskUpdate",
]
