from __future__ import annotations

from typing import Any

from pydantic import Field

from nbu.models.base import JsonModel, NbuModel
from nbu.models.slp import SLPDetails


class Schedule(JsonModel):
    """Readable schedule fields; the complete definition lives in Policy.raw."""

    schedule_name: str = ""
    schedule_type: str | None = None
    backup_type: str | None = None
    frequency_seconds: int | None = None
    start_window: list[dict[str, Any]] = Field(default_factory=list)
    include_dates: Any | None = None
    exclude_dates: Any | None = None
    storage_is_slp: bool | None = None
    backup_copies: dict[str, Any] | None = None


class Policy(NbuModel):
    name: str = ""
    policy_type: str | None = None
    active: bool | None = None
    clients: list[str] = Field(default_factory=list)
    schedules: list[Schedule] = Field(default_factory=list)
    backup_selections: list[str] = Field(default_factory=list)
    retention: Any | None = None
    storage: str | None = None
    storage_is_slp: bool | None = None
    slp: str | None = None
    slps: dict[str, SLPDetails] = Field(default_factory=dict)
