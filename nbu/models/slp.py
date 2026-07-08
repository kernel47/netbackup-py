from __future__ import annotations

from typing import Any

from pydantic import Field

from nbu.models.base import NbuModel


class SLPOperation(NbuModel):
    operation: str = ""
    target_storage: str | None = None
    retention: Any | None = None
    retention_type: str | None = None
    duplication: bool | None = None
    operation_index: int | None = None
    source_operation_index: int | None = None
    storage: dict[str, Any] | None = None


class SLP(NbuModel):
    name: str = ""
    active: bool | None = None
    status: str | None = None
    operations: list[SLPOperation] = Field(default_factory=list)
    retention: Any | None = None
    target_storage: str | None = None
