from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import Field

from nbu.models.base import NbuModel


class Severity(StrEnum):
    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class HealthCheck(NbuModel):
    name: str
    severity: Severity
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class HealthReport(NbuModel):
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    severity: Severity = Severity.UNKNOWN
    checks: list[HealthCheck] = Field(default_factory=list)

    @classmethod
    def from_checks(cls, checks: list[HealthCheck]) -> "HealthReport":
        order = {
            Severity.OK: 0,
            Severity.UNKNOWN: 1,
            Severity.WARNING: 2,
            Severity.CRITICAL: 3,
        }
        severity = max((check.severity for check in checks), key=lambda s: order[s], default=Severity.UNKNOWN)
        return cls(severity=severity, checks=checks)
