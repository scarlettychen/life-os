"""Daily planning service."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlmodel import Session

from lifeos.engine.scheduler import plan_day
from lifeos.models.timeblock import TimeBlock
from lifeos.repositories import TimeBlockRepository
from lifeos.schemas.planning import DayPlanResult
from lifeos.services.recommend import build_snapshot


def plan_and_persist(
    session: Session,
    *,
    now: datetime | None = None,
    persist: bool = True,
) -> DayPlanResult:
    """Build today's plan and optionally save proposed blocks to the database."""
    snapshot = build_snapshot(session, now=now)
    result = plan_day(snapshot)

    if persist and result.blocks:
        repo = TimeBlockRepository(session)
        day_start = snapshot.now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        db_blocks = [
            TimeBlock(
                task_id=b.task_id,
                title=b.title,
                start=b.start,
                end=b.end,
                status=b.status,
                kind=b.kind,
                rationale=b.rationale,
            )
            for b in result.blocks
        ]
        repo.replace_proposed_for_day(day_start, day_end, db_blocks)

    return result
