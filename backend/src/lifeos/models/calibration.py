"""Per-area estimation calibration factors (EMA of actual/estimated)."""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel

from lifeos.models.base import utcnow


class CalibrationFactor(SQLModel, table=True):
    __tablename__ = "calibration_factors"

    id: int | None = Field(default=None, primary_key=True)
    area_id: int | None = Field(
        default=None,
        foreign_key="areas.id",
        unique=True,
        description="Null = global fallback factor.",
    )
    ratio: float = Field(default=1.0, ge=0.1, le=5.0)
    sample_count: int = Field(default=0, ge=0)
    updated_at: datetime = Field(default_factory=utcnow)
