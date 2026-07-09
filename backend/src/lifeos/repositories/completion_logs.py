"""CompletionLog repository."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlmodel import col, select

from lifeos.models.completion_log import CompletionLog
from lifeos.repositories.base import BaseRepository


class CompletionLogRepository(BaseRepository[CompletionLog]):
    model = CompletionLog

    def list_since(self, since: datetime, *, limit: int = 2000) -> list[CompletionLog]:
        statement = (
            select(CompletionLog)
            .where(CompletionLog.completed_at >= since)
            .order_by(col(CompletionLog.completed_at).desc())
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def list_for_week(self, week_start: date, *, limit: int = 2000) -> list[CompletionLog]:
        week_end = week_start + timedelta(days=7)
        start_dt = datetime.combine(week_start, time.min)
        end_dt = datetime.combine(week_end, time.min)
        statement = (
            select(CompletionLog)
            .where(CompletionLog.completed_at >= start_dt)
            .where(CompletionLog.completed_at < end_dt)
            .order_by(col(CompletionLog.completed_at).desc())
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def list_for_goal_since(
        self,
        goal_id: int,
        since: datetime,
        *,
        limit: int = 500,
    ) -> list[CompletionLog]:
        statement = (
            select(CompletionLog)
            .where(CompletionLog.goal_id == goal_id)
            .where(CompletionLog.completed_at >= since)
            .order_by(col(CompletionLog.completed_at).desc())
            .limit(limit)
        )
        return list(self.session.exec(statement).all())
