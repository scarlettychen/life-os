"""End-to-end recommendation tests with a realistic student workload."""

from __future__ import annotations

from datetime import timedelta

from lifeos.engine.recommend import rank_tasks, recommend_next
from lifeos.models.enums import TaskStatus
from lifeos.schemas.snapshot import TaskSnapshot
from tests.fixtures.student_workload import NOW, conflict_snapshot, student_snapshot


def test_recommends_ap_calc_over_low_priority_admin() -> None:
    result = recommend_next(student_snapshot())
    assert result.top_pick is not None
    assert result.top_pick.title == "AP Calc problem set 7"
    assert result.eligible_count == 5  # 6 tasks minus 1 done


def test_isef_ranks_above_robotics_cad_and_personal() -> None:
    ranked = rank_tasks(student_snapshot())
    titles = [r.title for r in ranked]
    isef_idx = titles.index("ISEF abstract draft")
    cad_idx = titles.index("Swerve module CAD v2")
    admin_idx = titles.index("Organize downloads folder")
    assert isef_idx < cad_idx
    assert isef_idx < admin_idx


def test_done_tasks_excluded_from_ranking() -> None:
    ranked = rank_tasks(student_snapshot())
    assert all("Chemistry" not in r.title for r in ranked)


def test_pinned_task_jumps_to_top() -> None:
    snapshot = student_snapshot()
    pinned = TaskSnapshot(
        id=99,
        title="Pinned: email counselor",
        status=TaskStatus.TODO,
        priority=1,
        estimated_minutes=10,
        pinned=True,
        area_id=4,
    )
    snapshot = snapshot.model_copy(update={"tasks": [*snapshot.tasks, pinned]})
    result = recommend_next(snapshot)
    assert result.top_pick is not None
    assert result.top_pick.title == "Pinned: email counselor"


def test_conflict_snapshot_surfaces_multiple_issues() -> None:
    result = recommend_next(conflict_snapshot())
    kinds = {c.kind for c in result.conflicts}
    assert len(kinds) == 2
    # Urgent school work should still be recommended despite conflicts elsewhere.
    assert result.top_pick is not None
    assert "AP Calc" in result.top_pick.title or "Physics" in result.top_pick.title


def test_blocked_task_not_recommended() -> None:
    snapshot = student_snapshot()
    blocked = snapshot.tasks[0].model_copy(
        update={"status": TaskStatus.BLOCKED, "title": "Blocked ISEF draft"}
    )
    tasks = [blocked, *snapshot.tasks[1:]]
    snapshot = snapshot.model_copy(update={"tasks": tasks})
    ranked = rank_tasks(snapshot)
    assert all("Blocked ISEF" not in r.title for r in ranked)


def test_future_earliest_start_excluded() -> None:
    snapshot = student_snapshot()
    future = snapshot.tasks[2].model_copy(
        update={"earliest_start": NOW + timedelta(days=2)}
    )
    tasks = list(snapshot.tasks)
    tasks[2] = future
    snapshot = snapshot.model_copy(update={"tasks": tasks})
    ranked = rank_tasks(snapshot)
    assert all("CAD" not in r.title for r in ranked)
