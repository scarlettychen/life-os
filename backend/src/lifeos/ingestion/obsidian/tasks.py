"""Parse Obsidian Tasks-style checkbox lines."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime

from lifeos.models.enums import EnergyLevel, TaskStatus
from lifeos.utils.dates import parse_due

_CHECKBOX_RE = re.compile(
    r"^(\s*)- \[( |x|X)\] (.+)$",
)
_DUE_RE = re.compile(r"📅\s*(\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?)?)")
_DONE_RE = re.compile(r"✅\s*(\d{4}-\d{2}-\d{2})")
_ESTIMATE_RE = re.compile(r"⏱️\s*(\d+)")
_ENERGY_RE = re.compile(r"⚡\s*(low|medium|high)", re.IGNORECASE)
_BLOCK_ID_RE = re.compile(r"🆔\s*(\S+)")
_PRIORITY_HIGH = "⏫"
_PRIORITY_MED = "🔼"
_PRIORITY_LOW = "🔽"


@dataclass(frozen=True)
class ParsedTaskLine:
    line_number: int
    title: str
    status: TaskStatus
    priority: int
    estimated_minutes: int | None
    due_date: datetime | None
    completed_at: datetime | None
    energy_required: EnergyLevel
    is_deep_work: bool
    block_id: str | None
    source_ref: str


def parse_task_lines(body: str, *, relative_path: str) -> list[ParsedTaskLine]:
    """Extract checkbox tasks from a note body."""
    tasks: list[ParsedTaskLine] = []
    for line_no, raw in enumerate(body.splitlines(), start=1):
        match = _CHECKBOX_RE.match(raw)
        if not match:
            continue
        checked = match.group(2).lower() == "x"
        content = match.group(3).strip()
        parsed = _parse_task_content(content)
        block_id = parsed.pop("block_id")
        source_ref = _task_source_ref(relative_path, line_no, content, block_id)
        tasks.append(
            ParsedTaskLine(
                line_number=line_no,
                source_ref=source_ref,
                status=TaskStatus.DONE if checked else TaskStatus.TODO,
                block_id=block_id,
                **parsed,
            )
        )
    return tasks


def _parse_task_content(content: str) -> dict:
    title = content
    priority = 3
    estimated_minutes: int | None = None
    due_date: datetime | None = None
    completed_at: datetime | None = None
    energy_required = EnergyLevel.MEDIUM
    is_deep_work = "#deep" in content.lower()
    block_id: str | None = None

    if _PRIORITY_HIGH in content:
        priority = 5
    elif _PRIORITY_MED in content:
        priority = 4
    elif _PRIORITY_LOW in content:
        priority = 2

    if due_match := _DUE_RE.search(content):
        due_date = parse_due(due_match.group(1))

    if done_match := _DONE_RE.search(content):
        completed_at = parse_due(done_match.group(1))

    if est_match := _ESTIMATE_RE.search(content):
        estimated_minutes = int(est_match.group(1))

    if energy_match := _ENERGY_RE.search(content):
        energy_required = EnergyLevel(energy_match.group(1).lower())

    if block_match := _BLOCK_ID_RE.search(content):
        block_id = block_match.group(1)

    title = _strip_markers(title)
    return {
        "title": title,
        "priority": priority,
        "estimated_minutes": estimated_minutes,
        "due_date": due_date,
        "completed_at": completed_at,
        "energy_required": energy_required,
        "is_deep_work": is_deep_work,
        "block_id": block_id,
    }


def _strip_markers(text: str) -> str:
    """Remove task-plugin emoji markers from the visible title."""
    patterns = [
        _DUE_RE,
        _DONE_RE,
        _ESTIMATE_RE,
        _ENERGY_RE,
        _BLOCK_ID_RE,
        re.compile(r"🔁\s*.+"),
        re.compile(r"#\w+"),
    ]
    cleaned = text
    for pattern in patterns:
        cleaned = pattern.sub("", cleaned)
    for emoji in (_PRIORITY_HIGH, _PRIORITY_MED, _PRIORITY_LOW):
        cleaned = cleaned.replace(emoji, "")
    return " ".join(cleaned.split()).strip()


def _task_source_ref(
    relative_path: str,
    line_no: int,
    content: str,
    block_id: str | None,
) -> str:
    if block_id:
        return f"{relative_path}#id:{block_id}"
    normalized = re.sub(r"\s+", " ", content.strip().lower())
    digest = hashlib.sha256(f"{relative_path}:{line_no}:{normalized}".encode()).hexdigest()[:12]
    return f"{relative_path}#{digest}"
