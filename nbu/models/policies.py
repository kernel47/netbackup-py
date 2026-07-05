from __future__ import annotations

from typing import Any

from pydantic import Field

from nbu.models.base import NbuModel


class Schedule(NbuModel):
    name: str
    type: str | None = None
    retention: str | int | None = None
    frequency_seconds: int | None = None
    calendar: dict[str, Any] | None = None


class Policy(NbuModel):
    name: str
    policy_type: str | None = None
    active: bool | None = None
    clients: list[str] = Field(default_factory=list)
    schedules: list[Schedule] = Field(default_factory=list)
    backup_selections: list[str] = Field(default_factory=list)
    vmware_odata_filters: list[str] = Field(default_factory=list)
    retention: str | int | None = None
    storage: str | None = None
