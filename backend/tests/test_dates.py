"""Date parsing tests."""

from __future__ import annotations

from datetime import datetime

import pytest

from lifeos.utils.dates import parse_due


def test_parse_date_only_sets_end_of_day() -> None:
    due = parse_due("2026-02-05")
    assert due == datetime(2026, 2, 5, 23, 59, 59)


def test_parse_iso_datetime() -> None:
    due = parse_due("2026-02-05T08:00")
    assert due == datetime(2026, 2, 5, 8, 0)


def test_invalid_date_raises() -> None:
    with pytest.raises(ValueError):
        parse_due("not-a-date")
