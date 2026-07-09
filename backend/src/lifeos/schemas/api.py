"""API request/response bodies."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class TaskDoneBody(BaseModel):
    actual_minutes: int | None = Field(default=None, ge=0)
    energy_before: float | None = Field(default=None, ge=0.0, le=1.0)
    energy_after: float | None = Field(default=None, ge=0.0, le=1.0)


class ReviewBody(BaseModel):
    week: date | None = None
    dry_run: bool = False
    satisfaction: int | None = Field(default=None, ge=1, le=5)


class BriefBody(BaseModel):
    dry_run: bool = False


class CompletionResponse(BaseModel):
    task: dict
    log: dict
    observed_ratio: float
    updated_area_ratio: float | None
