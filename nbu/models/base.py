"""Shared Pydantic model helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NbuModel(BaseModel):
    """Base model preserving source payload for auditability."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    source: str = "api"
    raw: dict[str, Any] = Field(default_factory=dict)


class TimeRange(BaseModel):
    start_date: datetime | str | None = None
    end_date: datetime | str | None = None

