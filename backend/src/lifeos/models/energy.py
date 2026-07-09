"""Energy profile slots and observed energy logs."""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel

from lifeos.models.base import utcnow
from lifeos.models.enums import EnergyProfileSource


class EnergyProfileSlot(SQLModel, table=True):
    __tablename__ = "energy_profile_slots"

    id: int | None = Field(default=None, primary_key=True)
    day_of_week: int = Field(ge=0, le=6, description="0=Monday")
    start_hour: int = Field(ge=0, le=23)
    end_hour: int = Field(ge=1, le=24)
    predicted_energy: float = Field(ge=0.0, le=1.0)
    source: EnergyProfileSource = EnergyProfileSource.DEFAULT
    updated_at: datetime = Field(default_factory=utcnow)


class EnergyLog(SQLModel, table=True):
    __tablename__ = "energy_logs"

    id: int | None = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=utcnow)
    energy_level: float = Field(ge=0.0, le=1.0)
    mood: str | None = None
    context: str | None = None
    note: str | None = None
    task_id: int | None = Field(default=None, foreign_key="tasks.id")
