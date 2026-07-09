"""Map parsed Obsidian notes to LifeOS domain fields."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from lifeos.ingestion.obsidian.parser import ParsedNote
from lifeos.ingestion.obsidian.tasks import ParsedTaskLine
from lifeos.models.enums import GoalHorizon, GoalStatus, ProjectStatus

_WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


def note_source_ref(note: ParsedNote) -> str:
    """Stable reference for a note-backed entity."""
    note_id = note.frontmatter.get("id")
    if note_id:
        return str(note_id)
    return note.relative_path


def extract_wikilink_titles(value: Any) -> list[str]:
    """Pull link titles from a frontmatter wikilink field."""
    if value is None:
        return []
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, list):
        items = [str(v) for v in value]
    else:
        items = [str(value)]
    titles: list[str] = []
    for item in items:
        match = _WIKILINK_RE.search(item)
        titles.append(match.group(1) if match else item.strip())
    return titles


def map_area(note: ParsedNote) -> dict[str, Any]:
    meta = note.frontmatter
    key = str(meta.get("key") or meta.get("area") or _slug_from_path(note.relative_path))
    name = str(meta.get("name") or meta.get("title") or key.replace("-", " ").title())
    return {
        "key": key,
        "name": name,
        "target_allocation": float(meta.get("target_allocation", 0.0)),
        "color": meta.get("color"),
        "active": bool(meta.get("active", True)),
    }


def map_goal(note: ParsedNote, *, area_id: int | None) -> dict[str, Any]:
    meta = note.frontmatter
    return {
        "title": str(meta.get("title") or note.path.stem.replace("-", " ").title()),
        "description": meta.get("description"),
        "area_id": area_id,
        "horizon": _parse_horizon(meta.get("horizon")),
        "target_date": _parse_optional_date(meta.get("target_date")),
        "priority": int(meta.get("priority", 3)),
        "weight": float(meta.get("weight", 0.0)),
        "success_criteria": meta.get("success_criteria"),
        "status": _parse_goal_status(meta.get("status")),
        "progress": float(meta.get("progress", 0.0)),
    }


def map_project(note: ParsedNote, *, area_id: int | None, goal_id: int | None) -> dict[str, Any]:
    meta = note.frontmatter
    return {
        "title": str(meta.get("title") or note.path.stem.replace("-", " ").title()),
        "description": meta.get("description"),
        "area_id": area_id,
        "goal_id": goal_id,
        "status": _parse_project_status(meta.get("status")),
        "priority": int(meta.get("priority", 3)),
        "estimated_effort_hours": _optional_float(meta.get("estimated_effort_hours")),
        "progress": float(meta.get("progress", 0.0)),
    }


def map_task(
    line: ParsedTaskLine,
    *,
    project_id: int | None,
    goal_id: int | None,
    area_id: int | None,
) -> dict[str, Any]:
    return {
        "title": line.title,
        "project_id": project_id,
        "goal_id": goal_id,
        "area_id": area_id,
        "status": line.status,
        "priority": line.priority,
        "estimated_minutes": line.estimated_minutes,
        "due_date": line.due_date,
        "energy_required": line.energy_required,
        "is_deep_work": line.is_deep_work,
        "completed_at": line.completed_at,
    }


def note_type(note: ParsedNote) -> str | None:
    value = note.frontmatter.get("type")
    return str(value).lower() if value else None


def referenced_area_key(note: ParsedNote) -> str | None:
    area = note.frontmatter.get("area")
    return str(area) if area else None


def _slug_from_path(relative_path: str) -> str:
    stem = relative_path.rsplit("/", 1)[-1]
    if stem.endswith(".md"):
        stem = stem[:-3]
    return stem.lower().replace(" ", "-")


def _parse_horizon(value: Any) -> GoalHorizon:
    if value is None:
        return GoalHorizon.MEDIUM
    try:
        return GoalHorizon(str(value).lower())
    except ValueError:
        return GoalHorizon.MEDIUM


def _parse_goal_status(value: Any) -> GoalStatus:
    if value is None:
        return GoalStatus.ACTIVE
    try:
        return GoalStatus(str(value).lower())
    except ValueError:
        return GoalStatus.ACTIVE


def _parse_project_status(value: Any) -> ProjectStatus:
    if value is None:
        return ProjectStatus.PLANNED
    try:
        return ProjectStatus(str(value).lower())
    except ValueError:
        return ProjectStatus.PLANNED


def _parse_optional_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
