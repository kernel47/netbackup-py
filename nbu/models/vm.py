from __future__ import annotations

from datetime import datetime
from typing import Any

from nbu.models.base import NbuModel


class VMAsset(NbuModel):
    name: str
    uuid: str | None = None
    vcenter: str | None = None
    policies: list[str] = []
    last_backup: datetime | str | None = None
    backup_status: str | int | None = None
    protected: bool | None = None


def vm_asset_from_mapping(payload: dict[str, Any], source: str = "api") -> VMAsset:
    attrs = payload.get("attributes", payload)
    return VMAsset(
        name=attrs.get("displayName") or attrs.get("display_name") or attrs.get("name") or attrs.get("vmName") or attrs.get("vm_name"),
        uuid=attrs.get("uuid") or attrs.get("instanceUuid") or attrs.get("instance_uuid"),
        vcenter=attrs.get("vCenter") or attrs.get("vcenter"),
        policies=attrs.get("policies", []) or [],
        last_backup=attrs.get("lastBackup") or attrs.get("last_backup"),
        backup_status=attrs.get("backupStatus") or attrs.get("backup_status"),
        protected=attrs.get("protected"),
        raw=payload,
        source=source,
    )
