"""Unit tests for task scoring factors."""

from __future__ import annotations

from datetime import timedelta

from lifeos.engine.scoring import (
    compute_goal_alignment,
    compute_importance,
    compute_slack_minutes,
    compute_time_cost,
    compute_urgency,
    is_eligible,
    score_task,
)
from lifeos.models.enums import TaskStatus
from lifeos.schemas.snapshot import TaskSnapshot
from tests.fixtures.student_workload import NOW, student_snapshot


def test_ap_calc_more_urgent_than_robotics_cad() -> None:
    snapshot = student_snapshot()
    calc = next(t for t in snapshot.tasks if t.title.startswith("AP Calc"))
    cad = next(t for t in snapshot.tasks if "CAD" in t.title)

    assert compute_urgency(calc, now=NOW) > compute_urgency(cad, now=NOW)


def test_isef_has_higher_importance_than_personal_admin() -> None:
    snapshot = student_snapshot()
    isef = next(t for t in snapshot.tasks if "ISEF abstract" in t.title)
    admin = next(t for t in snapshot.tasks if "downloads" in t.title)

    assert compute_importance(isef, snapshot.goals, snapshot.projects) > compute_importance(
        admin, snapshot.goals, snapshot.projects
    )


def test_goal_linked_task_has_strong_alignment() -> None:
    snapshot = student_snapshot()
    isef = next(t for t in snapshot.tasks if "ISEF abstract" in t.title)
    admin = next(t for t in snapshot.tasks if "downloads" in t.title)

    assert compute_goal_alignment(isef, snapshot.goals, snapshot.projects) == 1.0
    assert compute_goal_alignment(admin, snapshot.goals, snapshot.projects) == 0.4


def test_quick_high_priority_task_scores_well_on_time_cost() -> None:
    importance = 0.8
    assert compute_time_cost(importance, 30) > compute_time_cost(importance, 180)


def test_negative_slack_means_infeasible() -> None:
    task = TaskSnapshot(
        id=99,
        title="Late lab",
        status=TaskStatus.TODO,
        priority=4,
        estimated_minutes=120,
        due_date=NOW + timedelta(minutes=30),
    )
    slack = compute_slack_minutes(task, now=NOW)
    assert slack is not None
    assert slack < 0
    assert compute_urgency(task, now=NOW) == 1.0


def test_done_tasks_are_ineligible() -> None:
    snapshot = student_snapshot()
    done = next(t for t in snapshot.tasks if t.status is TaskStatus.DONE)
    assert is_eligible(done, now=NOW) is False


def test_score_breakdown_sums_to_total() -> None:
    snapshot = student_snapshot()
    task = snapshot.tasks[0]
    breakdown = score_task(task, snapshot)
    assert abs(sum(breakdown.contributions.values()) - breakdown.total) < 1e-9
