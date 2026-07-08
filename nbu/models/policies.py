from __future__ import annotations

from typing import Any

from pydantic import Field

from nbu.models.base import NbuModel


class Schedule(NbuModel):
    name: str = ""
    type: str | None = None
    backup_type: str | None = None
    retention: Any | None = None
    retention_period: Any | None = None
    frequency_seconds: int | None = None
    include_dates: Any | None = None
    exclude_dates: Any | None = None
    start_window: list[dict[str, Any]] = Field(default_factory=list)
    storage: str | None = None
    storage_is_slp: bool | None = None
    slp_name: str | None = None
    slp_retention: Any | None = None
    slp_operation: dict[str, Any] | None = None


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
    slp_name: str | None = None
    slp_retention: Any | None = None
    slp_operation: dict[str, Any] | None = None
