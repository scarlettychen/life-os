"""Mark Obsidian checkbox tasks done in the vault."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from lifeos.config import Settings, get_settings
from lifeos.models.enums import SourceType
from lifeos.models.task import Task
from lifeos.services.sync import resolve_vault_path

_CHECKBOX_LINE = re.compile(r"^(\s*- \[)( |x|X)(\].*)$", re.MULTILINE)


def writeback_task_done(
    task: Task,
    *,
    completed_on: date | None = None,
    settings: Settings | None = None,
) -> Path | None:
    """Check off an Obsidian-sourced task in its vault note."""
    if task.source is not SourceType.OBSIDIAN or not task.source_ref:
        return None

    cfg = settings or get_settings()
    vault = resolve_vault_path(cfg)
    ref = task.source_ref
    path_part, _, locator = ref.partition("#")
    note_path = vault / path_part
    if not note_path.exists():
        return None

    text = note_path.read_text(encoding="utf-8")
    done_date = (completed_on or date.today()).isoformat()
    updated = _mark_line_done(text, locator=locator, done_date=done_date)
    if updated is None:
        return None
    note_path.write_text(updated, encoding="utf-8")
    return note_path


def _mark_line_done(text: str, *, locator: str, done_date: str) -> str | None:
    lines = text.splitlines(keepends=True)
    target_idx: int | None = None

    if locator.startswith("id:"):
        block_id = locator[3:]
        for i, line in enumerate(lines):
            if f"🆔 {block_id}" in line or f"🆔{block_id}" in line:
                target_idx = i
                break
    elif locator:
        digest = locator
        for i, line in enumerate(lines):
            if digest in line:
                target_idx = i
                break

    if target_idx is None:
        for i, line in enumerate(lines):
            if _CHECKBOX_LINE.match(line.rstrip("\n")) and "[ ]" in line:
                target_idx = i
                break

    if target_idx is None:
        return None

    line = lines[target_idx]
    match = _CHECKBOX_LINE.match(line.rstrip("\n"))
    if not match:
        return None
    if match.group(2).lower() == "x":
        return text  # already done

    new_line = f"{match.group(1)}x{match.group(3)}"
    if "✅" not in new_line:
        new_line = new_line.rstrip("\n") + f" ✅ {done_date}\n"
    lines[target_idx] = new_line if new_line.endswith("\n") else new_line + "\n"
    return "".join(lines)
