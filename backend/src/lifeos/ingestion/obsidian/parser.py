"""Parse Obsidian markdown notes (frontmatter + body)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import frontmatter

logger = logging.getLogger(__name__)

SKIP_DIRS = {".obsidian", ".git", ".trash", "__pycache__"}


@dataclass(frozen=True)
class ParsedNote:
    """A markdown file split into metadata and body."""

    path: Path
    relative_path: str
    frontmatter: dict
    body: str


def iter_markdown_files(vault_path: Path) -> list[Path]:
    """Return all ``.md`` files under ``vault_path``, skipping hidden/system dirs."""
    files: list[Path] = []
    for path in sorted(vault_path.rglob("*.md")):
        if any(part in SKIP_DIRS or part.startswith(".") for part in path.parts):
            continue
        files.append(path)
    return files


def parse_note(path: Path, *, vault_root: Path) -> ParsedNote | None:
    """Parse one markdown file. Returns ``None`` on malformed frontmatter."""
    try:
        post = frontmatter.load(path)
    except Exception:
        logger.warning("Skipping unreadable note: %s", path, exc_info=True)
        return None
    rel = path.relative_to(vault_root).as_posix()
    return ParsedNote(
        path=path,
        relative_path=rel,
        frontmatter=dict(post.metadata or {}),
        body=post.content or "",
    )
