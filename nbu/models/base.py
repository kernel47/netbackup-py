"""Shared model and JSON serialization helpers."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class JsonModel(BaseModel):
    """One serialization entry point for dictionaries and JSON text."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    def model_dump(
        self,
        *,
        mode: Literal["json", "python"] = "python",
        indent: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any] | str:
        """Return a dictionary, or JSON text with mode="json"."""
        if mode == "json":
            return super().model_dump_json(indent=indent, **kwargs)
        if mode != "python":
            raise ValueError("mode must be 'python' or 'json'")
        if indent is not None:
            raise ValueError("indent requires mode='json'")
        return super().model_dump(mode="python", **kwargs)

    @property
    def model_dump_json(self) -> None:
        raise AttributeError("Use model_dump(mode='json', indent=...) instead")


class NbuModel(JsonModel):
    """Top-level resource with one independent copy of its original API response."""

    source: str = "api"
    raw: dict[str, Any] = Field(default_factory=dict)

    @field_validator("raw", mode="before")
    @classmethod
    def copy_raw(cls, value: Any) -> Any:
        return deepcopy(value)


class TimeRange(JsonModel):
    start_date: datetime | str | None = None
    end_date: datetime | str | None = None
