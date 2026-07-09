"""Background scheduler for daily brief and weekly review."""

from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from lifeos.config import get_settings
from lifeos.db import session_scope
from lifeos.services.brief import write_daily_brief
from lifeos.services.review import write_weekly_review

logger = logging.getLogger(__name__)

_DAY_MAP = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}


def _run_brief_job() -> None:
    with session_scope() as session:
        result = write_daily_brief(session)
        logger.info("Daily brief written to %s", result.path)


def _run_review_job() -> None:
    with session_scope() as session:
        result = write_weekly_review(session)
        logger.info("Weekly review written to %s", result.path)


def run_daemon() -> None:
    """Block and fire scheduled brief + weekly review jobs."""
    settings = get_settings()
    brief_h, brief_m = _parse_time(settings.brief_time)
    review_h, review_m = _parse_time(settings.review_time)
    review_dow = _DAY_MAP.get(settings.review_day.lower().strip()[:3], 6)

    scheduler = BlockingScheduler()
    scheduler.add_job(
        _run_brief_job,
        CronTrigger(hour=brief_h, minute=brief_m),
        id="daily_brief",
        name="LifeOS daily brief",
    )
    scheduler.add_job(
        _run_review_job,
        CronTrigger(day_of_week=review_dow, hour=review_h, minute=review_m),
        id="weekly_review",
        name="LifeOS weekly review",
    )
    logger.info(
        "LifeOS daemon started — brief at %s, review on %s at %s",
        settings.brief_time,
        settings.review_day,
        settings.review_time,
    )
    scheduler.start()


def _parse_time(value: str) -> tuple[int, int]:
    parts = value.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid time format: {value!r} (expected HH:MM)")
    return int(parts[0]), int(parts[1])
