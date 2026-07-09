"""Overload engine tests."""

from __future__ import annotations

from lifeos.engine.overload import assess_overload
from tests.fixtures.student_workload import conflict_snapshot, student_snapshot


def test_green_on_normal_load() -> None:
    report = assess_overload(student_snapshot())
    assert report.severity.value == "green"


def test_red_on_infeasible() -> None:
    report = assess_overload(conflict_snapshot())
    assert report.severity.value == "red"
    assert report.cut_list
