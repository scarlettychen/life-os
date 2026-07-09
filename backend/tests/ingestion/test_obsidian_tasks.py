"""Checkbox task line parser tests."""

from __future__ import annotations

from lifeos.ingestion.obsidian.tasks import parse_task_lines
from lifeos.models.enums import EnergyLevel, TaskStatus

SAMPLE = """
## Tasks
- [ ] Draft ISEF abstract  ⏫ 📅 2026-02-06  ⏱️180  ⚡high  #deep
- [x] Collect lab data  ✅ 2026-02-01
- [ ] Problem set 7  📅 2026-02-05  ⏱️90  🔼
"""


def test_parses_open_task_with_markers() -> None:
    tasks = parse_task_lines(SAMPLE, relative_path="projects/isef.md")
    abstract = next(t for t in tasks if "abstract" in t.title.lower())
    assert abstract.status is TaskStatus.TODO
    assert abstract.priority == 5
    assert abstract.estimated_minutes == 180
    assert abstract.energy_required is EnergyLevel.HIGH
    assert abstract.is_deep_work is True
    assert abstract.due_date is not None


def test_parses_completed_task() -> None:
    tasks = parse_task_lines(SAMPLE, relative_path="projects/isef.md")
    done = next(t for t in tasks if "lab data" in t.title.lower())
    assert done.status is TaskStatus.DONE
    assert done.completed_at is not None


def test_stable_source_ref_per_line() -> None:
    first = parse_task_lines(SAMPLE, relative_path="projects/isef.md")
    second = parse_task_lines(SAMPLE, relative_path="projects/isef.md")
    assert first[0].source_ref == second[0].source_ref
