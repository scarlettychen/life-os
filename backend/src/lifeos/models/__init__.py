"""SQLModel data models for LifeOS.

Importing this package registers every table on ``SQLModel.metadata`` so that
``init_db`` can create the full schema.
"""

from __future__ import annotations

from lifeos.models.area import Area, AreaCreate, AreaUpdate
from lifeos.models.base import TimestampMixin, utcnow
from lifeos.models.calibration import CalibrationFactor
from lifeos.models.completion_log import CompletionLog, CompletionLogCreate
from lifeos.models.energy import EnergyLog, EnergyProfileSlot
from lifeos.models.enums import (
    EnergyLevel,
    EnergyProfileSource,
    GoalHorizon,
    GoalStatus,
    ProjectStatus,
    RestVerdict,
    SourceType,
    TaskStatus,
    TimeBlockKind,
    TimeBlockStatus,
)
from lifeos.models.goal import Goal, GoalCreate, GoalUpdate
from lifeos.models.project import Project, ProjectCreate, ProjectUpdate
from lifeos.models.task import Task, TaskCreate, TaskUpdate
from lifeos.models.timeblock import TimeBlock, TimeBlockCreate
from lifeos.models.weekly_review import WeeklyReview, WeeklyReviewCreate

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
    "TimeBlockKind",
    "TimeBlockStatus",
    "RestVerdict",
    "EnergyProfileSource",
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
    # completion / calibration / review (M4)
    "CompletionLog",
    "CompletionLogCreate",
    "CalibrationFactor",
    "WeeklyReview",
    "WeeklyReviewCreate",
    "EnergyProfileSlot",
    "EnergyLog",
    # timeblock
    "TimeBlock",
    "TimeBlockCreate",
]
