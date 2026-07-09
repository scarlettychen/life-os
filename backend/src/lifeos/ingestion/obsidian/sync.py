"""Sync Obsidian vault content into the LifeOS database."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from sqlmodel import Session

from lifeos.ingestion.obsidian.mapper import (
    extract_wikilink_titles,
    map_area,
    map_goal,
    map_project,
    map_task,
    note_source_ref,
    note_type,
    referenced_area_key,
)
from lifeos.ingestion.obsidian.parser import ParsedNote, iter_markdown_files, parse_note
from lifeos.ingestion.obsidian.tasks import parse_task_lines
from lifeos.repositories import AreaRepository, GoalRepository, ProjectRepository, TaskRepository

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    areas: int = 0
    goals: int = 0
    projects: int = 0
    tasks: int = 0
    dropped_tasks: int = 0
    skipped_files: int = 0
    warnings: list[str] = field(default_factory=list)


def sync_vault(vault_path: Path, session: Session) -> SyncResult:
    """Full vault scan → idempotent upsert of areas, goals, projects, and tasks."""
    vault_path = vault_path.expanduser().resolve()
    if not vault_path.is_dir():
        raise FileNotFoundError(f"Vault path does not exist: {vault_path}")

    result = SyncResult()
    notes = _load_notes(vault_path, result)

    area_repo = AreaRepository(session)
    goal_repo = GoalRepository(session)
    project_repo = ProjectRepository(session)
    task_repo = TaskRepository(session)

    area_ids = _sync_areas(notes, area_repo, result)
    goal_ids = _sync_goals(notes, goal_repo, area_ids, result)
    project_ids = _sync_projects(
        notes, project_repo, goal_repo, area_repo, area_ids, goal_ids, result
    )
    seen_task_refs = _sync_tasks(notes, task_repo, project_ids, goal_ids, area_ids, result)
    result.dropped_tasks = task_repo.mark_missing_obsidian_dropped(seen_task_refs)

    return result


def _load_notes(vault_path: Path, result: SyncResult) -> list[ParsedNote]:
    notes: list[ParsedNote] = []
    for path in iter_markdown_files(vault_path):
        parsed = parse_note(path, vault_root=vault_path)
        if parsed is None:
            result.skipped_files += 1
            continue
        notes.append(parsed)
    return notes


def _sync_areas(
    notes: list[ParsedNote],
    area_repo: AreaRepository,
    result: SyncResult,
) -> dict[str, int]:
    """Return area-key → database id."""
    key_to_id: dict[str, int] = {}

    typed = [n for n in notes if note_type(n) == "area"]
    for note in typed:
        data = map_area(note)
        area = area_repo.upsert_obsidian(note_source_ref(note), data)
        assert area.id is not None
        key_to_id[area.key] = area.id
        result.areas += 1

    # Auto-create areas referenced by goals/projects.
    for note in notes:
        key = referenced_area_key(note)
        if not key or key in key_to_id:
            continue
        area = area_repo.upsert_obsidian(
            f"area:{key}",
            {
                "key": key,
                "name": key.replace("-", " ").title(),
                "target_allocation": 0.0,
                "active": True,
            },
        )
        assert area.id is not None
        key_to_id[key] = area.id
        result.areas += 1

    for area in area_repo.list(limit=500):
        assert area.id is not None
        key_to_id.setdefault(area.key, area.id)

    return key_to_id


def _sync_goals(
    notes: list[ParsedNote],
    goal_repo: GoalRepository,
    area_ids: dict[str, int],
    result: SyncResult,
) -> dict[str, int]:
    """Return goal title → database id."""
    title_to_id: dict[str, int] = {}

    for note in notes:
        if note_type(note) != "goal":
            continue
        area_id = _resolve_area_id(note, area_ids)
        goal = goal_repo.upsert_obsidian(note_source_ref(note), map_goal(note, area_id=area_id))
        assert goal.id is not None
        title_to_id[goal.title] = goal.id
        result.goals += 1

    for goal in goal_repo.list(limit=500):
        assert goal.id is not None
        title_to_id.setdefault(goal.title, goal.id)

    return title_to_id


def _sync_projects(
    notes: list[ParsedNote],
    project_repo: ProjectRepository,
    goal_repo: GoalRepository,
    area_repo: AreaRepository,
    area_ids: dict[str, int],
    goal_ids: dict[str, int],
    result: SyncResult,
) -> dict[str, int]:
    """Return project source_ref → database id."""
    ref_to_id: dict[str, int] = {}

    for note in notes:
        if note_type(note) != "project":
            continue
        area_id = _resolve_area_id(note, area_ids)
        goal_id = _resolve_goal_id(note, goal_repo, goal_ids)
        project = project_repo.upsert_obsidian(
            note_source_ref(note),
            map_project(note, area_id=area_id, goal_id=goal_id),
        )
        assert project.id is not None
        ref_to_id[note_source_ref(note)] = project.id
        result.projects += 1

    return ref_to_id


def _sync_tasks(
    notes: list[ParsedNote],
    task_repo: TaskRepository,
    project_ids: dict[str, int],
    goal_ids: dict[str, int],
    area_ids: dict[str, int],
    result: SyncResult,
) -> set[str]:
    seen: set[str] = set()

    for note in notes:
        ntype = note_type(note)
        project_id = project_ids.get(note_source_ref(note)) if ntype == "project" else None
        goal_id = None
        area_id = _resolve_area_id(note, area_ids)

        if ntype == "goal":
            goal_id = goal_ids.get(str(note.frontmatter.get("title") or note.path.stem))
        elif ntype == "project":
            titles = extract_wikilink_titles(note.frontmatter.get("goals"))
            if titles:
                goal_id = goal_ids.get(titles[0])

        for line in parse_task_lines(note.body, relative_path=note.relative_path):
            task_repo.upsert_obsidian(
                line.source_ref,
                map_task(
                    line,
                    project_id=project_id,
                    goal_id=goal_id,
                    area_id=area_id,
                ),
            )
            seen.add(line.source_ref)
            result.tasks += 1

    return seen


def _resolve_area_id(note: ParsedNote, area_ids: dict[str, int]) -> int | None:
    key = referenced_area_key(note)
    if key is None:
        return None
    return area_ids.get(key)


def _resolve_goal_id(
    note: ParsedNote,
    goal_repo: GoalRepository,
    goal_ids: dict[str, int],
) -> int | None:
    titles = extract_wikilink_titles(note.frontmatter.get("goals"))
    if not titles:
        return None
    title = titles[0]
    if title in goal_ids:
        return goal_ids[title]
    goal = goal_repo.get_by_title(title)
    if goal is not None and goal.id is not None:
        return goal.id
    return None
