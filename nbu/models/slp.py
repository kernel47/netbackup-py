from __future__ import annotations

from pydantic import Field

from nbu.models.base import NbuModel


class SLPOperation(NbuModel):
    operation: str
    target_storage: str | None = None
    retention: str | int | None = None
    duplication: bool | None = None


class SLP(NbuModel):
    name: str
    status: str | None = None
    operations: list[SLPOperation] = Field(default_factory=list)
    retention: str | int | None = None
    target_storage: str | None = None
