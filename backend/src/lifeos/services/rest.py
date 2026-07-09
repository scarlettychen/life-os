"""Rest feasibility service."""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Session

from lifeos.engine.breaks import evaluate_rest
from lifeos.schemas.planning import RestResult
from lifeos.services.recommend import build_snapshot


def check_rest(
    session: Session,
    *,
    hours: float,
    now: datetime | None = None,
) -> RestResult:
    snapshot = build_snapshot(session, now=now)
    return evaluate_rest(snapshot, hours=hours)
