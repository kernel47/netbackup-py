"""Shared Pydantic model helpers."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NbuModel(BaseModel):
    """Base model preserving source payload for auditability."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    source: str = "api"
    raw: dict[str, Any] = Field(default_factory=dict)

    @field_validator("raw", mode="before")
    @classmethod
    def copy_raw(cls, value: Any) -> Any:
        return deepcopy(value)

    def to_api(self) -> dict[str, Any]:
        """Return the original API payload, without normalized or resolved fields."""
        return deepcopy(self.raw)

    @property
    def api_attributes(self) -> dict[str, Any]:
        """Return all original attributes, including unmodeled workload fields."""
        data = self.raw.get("data")
        resource = data if isinstance(data, dict) else self.raw
        attrs = resource.get("attributes")
        return deepcopy(attrs if isinstance(attrs, dict) else resource)


class TimeRange(BaseModel):
    start_date: datetime | str | None = None
    end_date: datetime | str | None = None
