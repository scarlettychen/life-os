"""Obsidian markdown parser tests."""

from __future__ import annotations

from pathlib import Path

from lifeos.ingestion.obsidian.parser import parse_note

VAULT = Path(__file__).resolve().parents[1] / "fixtures" / "vault"


def test_parse_project_frontmatter() -> None:
    path = VAULT / "projects" / "isef-research.md"
    note = parse_note(path, vault_root=VAULT)
    assert note is not None
    assert note.frontmatter["type"] == "project"
    assert note.frontmatter["area"] == "isef"
    assert "Draft ISEF abstract" in note.body
