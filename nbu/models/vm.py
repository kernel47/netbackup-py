from __future__ import annotations

from datetime import datetime

from pydantic import Field

from nbu.models.base import NbuModel


class VMAsset(NbuModel):
    name: str
    uuid: str | None = None
    vcenter: str | None = None
    policies: list[str] = Field(default_factory=list)
    last_backup: datetime | str | None = None
    backup_status: str | int | None = None
    protected: bool | None = None
