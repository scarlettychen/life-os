"""Date/time parsing helpers."""

from __future__ import annotations

from datetime import datetime


def parse_due(value: str) -> datetime:
    """Parse a due date from CLI or markdown markers.

    Accepts:
    - ``YYYY-MM-DD`` (due end of that day, 23:59:59)
    - ISO datetimes (``YYYY-MM-DDTHH:MM`` or with timezone)
    """
    text = value.strip()
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        due = datetime.strptime(text, "%Y-%m-%d")
        return due.replace(hour=23, minute=59, second=59)
    return datetime.fromisoformat(text)
