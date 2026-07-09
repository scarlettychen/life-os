"""Enumerations shared across the data models.

All enums subclass :class:`enum.StrEnum` so they serialize cleanly to JSON and
store as readable text in the database.
"""

from __future__ import annotations

from enum import StrEnum


class GoalHorizon(StrEnum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class GoalStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    DONE = "done"
    DROPPED = "dropped"


class ProjectStatus(StrEnum):
    PLANNED = "planned"
    ACTIVE = "active"
    BLOCKED = "blocked"
    DONE = "done"
    DROPPED = "dropped"


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    DROPPED = "dropped"


class EnergyLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SourceType(StrEnum):
    MANUAL = "manual"
    OBSIDIAN = "obsidian"
    GCAL = "gcal"


class TimeBlockStatus(StrEnum):
    PROPOSED = "proposed"
    COMMITTED = "committed"
    DONE = "done"
    MISSED = "missed"


class TimeBlockKind(StrEnum):
    WORK = "work"
    BREAK = "break"
    BUFFER = "buffer"
    REST = "rest"


class RestVerdict(StrEnum):
    YES = "yes"
    PARTIAL = "partial"
    NO = "no"


class EnergyProfileSource(StrEnum):
    DEFAULT = "default"
    LEARNED = "learned"
