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
    retention: str | int | None = None
    storage: str | None = None


def policy_from_mapping(payload: dict[str, Any], source: str = "api") -> Policy:
    attrs = payload.get("attributes", payload)
    schedules = [
        Schedule(name=s.get("name") or s.get("scheduleName"), type=s.get("type"), raw=s, source=source)
        for s in attrs.get("schedules", []) or []
    ]
    return Policy(
        name=attrs.get("policyName") or attrs.get("policy_name") or attrs.get("name"),
        policy_type=attrs.get("policyType") or attrs.get("policy_type"),
        active=attrs.get("active"),
        clients=attrs.get("clients", []) or [],
        schedules=schedules,
        backup_selections=attrs.get("backupSelections") or attrs.get("backup_selections") or [],
        retention=attrs.get("retention"),
        storage=attrs.get("storage") or attrs.get("storageUnit"),
        raw=payload,
        source=source,
    )
