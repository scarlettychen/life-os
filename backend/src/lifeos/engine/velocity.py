"""Goal velocity flags — stalling and off-pace detection."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from pydantic import BaseModel

from lifeos.models.enums import GoalStatus
from lifeos.schemas.snapshot import CompletionLogSnapshot, GoalSnapshot


class GoalVelocityFlag(BaseModel):
    goal_id: int
    title: str
    kind: str
    message: str


def flag_goal_velocity(
    goals: dict[int, GoalSnapshot],
    completions: list[CompletionLogSnapshot],
    *,
    now: datetime,
    stalling_days: int = 14,
) -> list[GoalVelocityFlag]:
    """Surface goals that are stalling or off pace for their target date."""
    flags: list[GoalVelocityFlag] = []
    cutoff = now - timedelta(days=stalling_days)

    for goal in goals.values():
        if goal.status != GoalStatus.ACTIVE:
            continue

        recent = [
            log
            for log in completions
            if log.goal_id == goal.id and log.completed_at >= cutoff
        ]

        if goal.progress < 0.05 and not recent:
            flags.append(
                GoalVelocityFlag(
                    goal_id=goal.id,
                    title=goal.title,
                    kind="stalling",
                    message=f"No progress in {stalling_days} days — consider a next action.",
                )
            )
            continue

        if goal.target_date is not None:
            days_left = (goal.target_date - now.date()).days
            if days_left <= 0:
                continue
            # Linear pace: expect progress proportional to elapsed horizon.
            horizon_days = _horizon_days(goal.target_date, goal.horizon, now.date())
            expected = max(0.0, 1.0 - (days_left / horizon_days))
            if goal.progress + 0.15 < expected:
                flags.append(
                    GoalVelocityFlag(
                        goal_id=goal.id,
                        title=goal.title,
                        kind="off_pace",
                        message=(
                            f"Progress {goal.progress:.0%} vs ~{expected:.0%} expected "
                            f"with {days_left} day(s) left."
                        ),
                    )
                )

    return flags


def _horizon_days(target_date: date, horizon, reference: date) -> int:
    """Approximate planning horizon in days for pace math."""
    days_to_target = max(1, (target_date - reference).days)
    from lifeos.models.enums import GoalHorizon

    if horizon is GoalHorizon.SHORT:
        return max(days_to_target, 30)
    if horizon is GoalHorizon.MEDIUM:
        return max(days_to_target, 90)
    return max(days_to_target, 365)
