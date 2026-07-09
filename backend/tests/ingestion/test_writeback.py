"""Managed-block writeback tests."""

from __future__ import annotations

from pathlib import Path

from lifeos.ingestion.obsidian.writeback import write_managed_block


def test_write_managed_block_inserts(tmp_path: Path) -> None:
    path = tmp_path / "note.md"
    path.write_text("# Daily\n\nSome notes.\n", encoding="utf-8")
    write_managed_block(path, block_id="daily-brief", content="## Plan\n- Task A\n")
    text = path.read_text(encoding="utf-8")
    assert "lifeos:begin daily-brief" in text
    assert "## Plan" in text
    assert "Some notes." in text


def test_write_managed_block_replaces_existing(tmp_path: Path) -> None:
    path = tmp_path / "note.md"
    write_managed_block(path, block_id="daily-brief", content="## v1\n")
    write_managed_block(path, block_id="daily-brief", content="## v2\n")
    text = path.read_text(encoding="utf-8")
    assert "## v2" in text
    assert "## v1" not in text
