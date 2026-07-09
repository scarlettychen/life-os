"""Overload assessment service."""

from __future__ import annotations

from sqlmodel import Session

from lifeos.engine.overload import OverloadReport, assess_overload
from lifeos.schemas.snapshot import EngineConfig
from lifeos.services.recommend import build_snapshot


def check_overload(
    session: Session,
    *,
    config: EngineConfig | None = None,
) -> OverloadReport:
    snapshot = build_snapshot(session, config=config)
    return assess_overload(snapshot)
