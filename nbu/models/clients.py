from __future__ import annotations

from pydantic import Field

from nbu.models.base import NbuModel


class Client(NbuModel):
    name: str
    os: str | None = None
    hardware: str | None = None
    policies: list[str] = Field(default_factory=list)
    active: bool | None = None
    last_backup_status: str | int | None = None
