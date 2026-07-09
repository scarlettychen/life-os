"""Balance boost affects ranking for underserved areas."""

from __future__ import annotations

from datetime import datetime

from lifeos.engine.scoring import score_task
from lifeos.models.enums import TaskStatus
from lifeos.schemas.snapshot import AreaSnapshot, EngineSnapshot, TaskSnapshot


def test_balance_boost_raises_score_for_underserved_area() -> None:
    task = TaskSnapshot(
        id=1,
        title="Personal admin",
        status=TaskStatus.TODO,
        priority=2,
        estimated_minutes=30,
        area_id=4,
    )
    base = EngineSnapshot(
        now=datetime(2026, 2, 4, 18, 0),
        tasks=[task],
        areas={4: AreaSnapshot(id=4, key="personal", target_allocation=0.10)},
        balance_drift={4: 0.10},
    )
    without = base.model_copy(update={"balance_drift": {4: 0.0}})
    boosted = score_task(task, base)
    plain = score_task(task, without)
    assert boosted.total > plain.total
    assert boosted.balance_boost > 0
