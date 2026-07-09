"""Realistic student workload for engine tests.

Scenario: Wednesday evening, juggling school, ISEF research, competitive
robotics, and low-priority personal admin.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from lifeos.models.enums import GoalHorizon, ProjectStatus, TaskStatus
from lifeos.schemas.snapshot import (
    AreaSnapshot,
    EngineConfig,
    EngineSnapshot,
    GoalSnapshot,
    ProjectSnapshot,
    TaskSnapshot,
)

# Fixed reference time: Wednesday, Feb 4 2026 at 6:00 PM.
NOW = datetime(2026, 2, 4, 18, 0)


def student_snapshot(*, now: datetime = NOW, config: EngineConfig | None = None) -> EngineSnapshot:
    """A typical overloaded week for a competitive student."""
    cfg = config or EngineConfig(daily_capacity_minutes=240)

    areas = {
        1: AreaSnapshot(id=1, key="school", target_allocation=0.30),
        2: AreaSnapshot(id=2, key="robotics", target_allocation=0.35),
        3: AreaSnapshot(id=3, key="isef", target_allocation=0.25),
        4: AreaSnapshot(id=4, key="personal", target_allocation=0.10),
    }

    goals = {
        1: GoalSnapshot(
            id=1,
            title="Win State Championship",
            priority=5,
            weight=0.9,
            horizon=GoalHorizon.LONG,
        ),
        2: GoalSnapshot(
            id=2,
            title="Publish ISEF research paper",
            priority=5,
            weight=0.95,
            horizon=GoalHorizon.LONG,
        ),
        3: GoalSnapshot(
            id=3,
            title="Maintain strong GPA",
            priority=4,
            weight=0.7,
            horizon=GoalHorizon.MEDIUM,
        ),
    }

    projects = {
        1: ProjectSnapshot(
            id=1,
            title="Swerve Drivetrain",
            goal_id=1,
            area_id=2,
            priority=4,
            status=ProjectStatus.ACTIVE,
        ),
        2: ProjectSnapshot(
            id=2,
            title="ISEF Research Paper",
            goal_id=2,
            area_id=3,
            priority=5,
            status=ProjectStatus.ACTIVE,
        ),
        3: ProjectSnapshot(
            id=3,
            title="AP Calculus BC",
            goal_id=3,
            area_id=1,
            priority=4,
            status=ProjectStatus.ACTIVE,
        ),
    }

    tasks = [
        TaskSnapshot(
            id=1,
            title="ISEF abstract draft",
            status=TaskStatus.TODO,
            priority=5,
            estimated_minutes=180,
            due_date=now + timedelta(hours=30),
            is_hard_deadline=True,
            project_id=2,
            goal_id=2,
            area_id=3,
        ),
        TaskSnapshot(
            id=2,
            title="AP Calc problem set 7",
            status=TaskStatus.TODO,
            priority=4,
            estimated_minutes=90,
            due_date=now + timedelta(hours=14),
            is_hard_deadline=True,
            project_id=3,
            goal_id=3,
            area_id=1,
        ),
        TaskSnapshot(
            id=3,
            title="Swerve module CAD v2",
            status=TaskStatus.TODO,
            priority=4,
            estimated_minutes=120,
            due_date=now + timedelta(days=4),
            project_id=1,
            goal_id=1,
            area_id=2,
        ),
        TaskSnapshot(
            id=4,
            title="Reply to team Slack",
            status=TaskStatus.TODO,
            priority=2,
            estimated_minutes=15,
            project_id=1,
            area_id=2,
        ),
        TaskSnapshot(
            id=5,
            title="Organize downloads folder",
            status=TaskStatus.TODO,
            priority=1,
            estimated_minutes=30,
            area_id=4,
        ),
        TaskSnapshot(
            id=6,
            title="Chemistry lab write-up",
            status=TaskStatus.DONE,
            priority=3,
            estimated_minutes=60,
            area_id=1,
        ),
    ]

    return EngineSnapshot(
        now=now,
        tasks=tasks,
        goals=goals,
        projects=projects,
        areas=areas,
        config=cfg,
    )


def conflict_snapshot(*, now: datetime = NOW) -> EngineSnapshot:
    """Workload with infeasible deadline and same-day overload."""
    base = student_snapshot(now=now)
    extra = [
        # Infeasible: 3 hours of work due in 2 hours.
        TaskSnapshot(
            id=10,
            title="Physics lab report",
            status=TaskStatus.TODO,
            priority=4,
            estimated_minutes=180,
            due_date=now + timedelta(hours=2),
            is_hard_deadline=True,
            area_id=1,
            goal_id=3,
        ),
        # Friday overload: 300 min total on one day (capacity 240).
        TaskSnapshot(
            id=11,
            title="History essay draft",
            status=TaskStatus.TODO,
            priority=3,
            estimated_minutes=120,
            due_date=datetime(2026, 2, 6, 23, 59),
            area_id=1,
        ),
        TaskSnapshot(
            id=12,
            title="Robotics scouting spreadsheet",
            status=TaskStatus.TODO,
            priority=3,
            estimated_minutes=90,
            due_date=datetime(2026, 2, 6, 17, 0),
            area_id=2,
            project_id=1,
        ),
        TaskSnapshot(
            id=13,
            title="ISEF data analysis",
            status=TaskStatus.TODO,
            priority=5,
            estimated_minutes=90,
            due_date=datetime(2026, 2, 6, 20, 0),
            area_id=3,
            project_id=2,
            goal_id=2,
        ),
    ]
    return base.model_copy(update={"tasks": [*base.tasks, *extra]})
