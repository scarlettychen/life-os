"""Area — a top-level life domain (school, robotics, isef, personal, ...).

Areas are the buckets the decision engine balances across.
"""

from __future__ import annotations

from sqlmodel import Field, SQLModel

from lifeos.models.base import TimestampMixin


class AreaBase(SQLModel):
    key: str = Field(index=True, description="Unique slug, e.g. 'robotics'")
    name: str
    target_allocation: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Desired share of discretionary time (0-1).",
    )
    color: str | None = None
    active: bool = True


class Area(AreaBase, TimestampMixin, table=True):
    __tablename__ = "areas"

    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)


class AreaCreate(AreaBase):
    pass


class AreaUpdate(SQLModel):
    key: str | None = None
    name: str | None = None
    target_allocation: float | None = Field(default=None, ge=0.0, le=1.0)
    color: str | None = None
    active: bool | None = None
