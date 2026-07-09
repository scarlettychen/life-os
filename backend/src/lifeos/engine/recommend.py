"""Orchestrate ranking and next-task recommendation."""

from __future__ import annotations

from lifeos.engine.conflicts import detect_conflicts
from lifeos.engine.scoring import is_eligible, score_task
from lifeos.schemas.results import RankedTask, RecommendationResult
from lifeos.schemas.snapshot import EngineSnapshot


def rank_tasks(snapshot: EngineSnapshot) -> list[RankedTask]:
    """Score and sort all eligible tasks (highest score first).

  Pinned tasks are always placed above non-pinned tasks.
    """
    ranked: list[RankedTask] = []
    for task in snapshot.tasks:
        if not is_eligible(task, now=snapshot.now):
            continue
        breakdown = score_task(task, snapshot)
        ranked.append(
            RankedTask(
                task_id=task.id,
                title=task.title,
                score=breakdown.total,
                breakdown=breakdown,
                eligible=True,
                pinned=task.pinned,
            )
        )

    ranked.sort(key=lambda r: (not r.pinned, -r.score, r.task_id))
    return ranked


def recommend_next(snapshot: EngineSnapshot) -> RecommendationResult:
    """Rank eligible tasks, detect conflicts, and pick the top recommendation."""
    eligible_tasks = [t for t in snapshot.tasks if is_eligible(t, now=snapshot.now)]
    ranked = rank_tasks(snapshot)
    conflicts = detect_conflicts(snapshot, tasks=eligible_tasks)
    top_pick = ranked[0] if ranked else None

    return RecommendationResult(
        ranked=ranked,
        conflicts=conflicts,
        top_pick=top_pick,
        eligible_count=len(eligible_tasks),
    )
