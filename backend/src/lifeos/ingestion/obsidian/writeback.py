"""Safe write-back of managed blocks into Obsidian notes."""

from __future__ import annotations

import re
from pathlib import Path

_BEGIN = "<!-- lifeos:begin {block_id} -->"
_END = "<!-- lifeos:end {block_id} -->"


def write_managed_block(path: Path, *, block_id: str, content: str) -> None:
    """Insert or replace a managed block in ``path`` without touching other content."""
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    begin = _BEGIN.format(block_id=block_id)
    end = _END.format(block_id=block_id)
    block = f"{begin}\n{content.rstrip()}\n{end}"

    pattern = re.compile(
        rf"{re.escape(begin)}.*?{re.escape(end)}",
        re.DOTALL,
    )
    if pattern.search(text):
        updated = pattern.sub(block, text)
    else:
        updated = text.rstrip() + ("\n\n" if text.strip() else "") + block + "\n"

    path.write_text(updated, encoding="utf-8")
