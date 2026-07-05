from __future__ import annotations

from datetime import datetime

from pydantic import Field

from nbu.models.base import NbuModel


class VMwareSelection(NbuModel):
    raw: str
    filter: str | None = None
    odata_filter: str | None = None
    resolved: bool = False


class VMAsset(NbuModel):
    name: str
    uuid: str | None = None
    vcenter: str | None = None
    asset_type: str | None = None
    cluster: str | None = None
    esx_server: str | None = None
    policies: list[str] = Field(default_factory=list)
    last_backup: datetime | str | None = None
    backup_status: str | int | None = None
    protected: bool | None = None
