"""Task completion logging and calibration updates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlmodel import Session

from lifeos.engine.calibration import update_ema_ratio
from lifeos.ingestion.obsidian.task_writeback import writeback_task_done
from lifeos.models.base import utcnow as log_timestamp
from lifeos.models.completion_log import CompletionLog, CompletionLogCreate
from lifeos.models.task import Task
from lifeos.repositories import (
    CalibrationRepository,
    CompletionLogRepository,
    ProjectRepository,
    TaskRepository,
)
from lifeos.schemas.snapshot import EngineConfig
from lifeos.services.energy import record_energy_observation


@dataclass
class CompletionResult:
    task: Task
    log: CompletionLog
    observed_ratio: float
    updated_area_ratio: float | None
    vault_path: str | None = None


def complete_task(
    session: Session,
    task_id: int,
    *,
    actual_minutes: int | None = None,
    energy_before: float | None = None,
    energy_after: float | None = None,
    config: EngineConfig | None = None,
    completed_at: datetime | None = None,
    write_vault: bool = True,
) -> CompletionResult:
    """Mark a task done, log completion, calibrate, and optionally write back to vault."""
    cfg = config or EngineConfig()
    repo = TaskRepository(session)
    task = repo.get(task_id)
    if task is None:
        raise ValueError(f"Task {task_id} not found")

    estimate = task.estimated_minutes or cfg.default_estimate_minutes
    actual = actual_minutes if actual_minutes is not None else estimate
    stamp = completed_at or log_timestamp()

    done = repo.mark_done(task_id, actual_minutes=actual)
    assert done is not None

    goal_id = _resolve_goal_id(task, session)
    log = CompletionLogRepository(session).create(
        CompletionLog.model_validate(
            CompletionLogCreate(
                task_id=task_id,
                area_id=task.area_id,
                goal_id=goal_id,
                title=task.title,
                estimated_minutes=estimate,
                actual_minutes=actual,
                energy_before=energy_before,
                energy_after=energy_after,
                completed_at=stamp,
            )
        )
    )

    if energy_before is not None:
        record_energy_observation(
            session,
            energy_level=energy_before,
            observed_at=stamp,
            task_id=task_id,
            context="before_task",
        )
    if energy_after is not None:
        record_energy_observation(
            session,
            energy_level=energy_after,
            observed_at=stamp,
            task_id=task_id,
            context="after_task",
        )

    observed_ratio = actual / max(estimate, 1)
    updated_area_ratio: float | None = None
    cal_repo = CalibrationRepository(session)

    if task.area_id is not None:
        current = cal_repo.get_for_area(task.area_id)
        new_ratio = update_ema_ratio(
            current.ratio if current else None,
            observed_ratio,
            alpha=cfg.calibration_ema_alpha,
        )
        cal_repo.save_ratio(task.area_id, ratio=new_ratio)
        updated_area_ratio = new_ratio
    else:
        current = cal_repo.get_for_area(None)
        new_ratio = update_ema_ratio(
            current.ratio if current else None,
            observed_ratio,
            alpha=cfg.calibration_ema_alpha,
        )
        cal_repo.save_ratio(None, ratio=new_ratio)

    vault_written: str | None = None
    if write_vault:
        path = writeback_task_done(done, completed_on=stamp.date())
        if path is not None:
            vault_written = str(path)

    return CompletionResult(
        task=done,
        log=log,
        observed_ratio=observed_ratio,
        updated_area_ratio=updated_area_ratio,
        vault_path=vault_written,
    )


def _resolve_goal_id(task: Task, session: Session) -> int | None:
    if task.goal_id is not None:
        return task.goal_id
    if task.project_id is not None:
        project = ProjectRepository(session).get(task.project_id)
        if project is not None:
            return project.goal_id
    return None
