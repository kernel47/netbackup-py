from __future__ import annotations

from datetime import datetime
from typing import Any

from nbu.models.base import NbuModel


class Image(NbuModel):
    image_id: str
    backup_id: str | None = None
    client: str | None = None
    policy: str | None = None
    policy_type: str | None = None
    schedule: str | None = None
    schedule_type: str | None = None
    backup_time: datetime | str | None = None
    expiration_time: datetime | str | None = None
    retention_level: str | int | None = None
    copy_number: int | None = None
    storage_location: str | None = None
    kilobytes: int | None = None


def image_from_mapping(payload: dict[str, Any], source: str = "api") -> Image:
    attrs = payload.get("attributes", payload)
    return Image(
        image_id=attrs.get("imageId")
        or attrs.get("image_id")
        or attrs.get("id")
        or attrs.get("backupId")
        or attrs.get("backup_id")
        or payload.get("id"),
        backup_id=attrs.get("backupId") or attrs.get("backup_id") or payload.get("id"),
        client=attrs.get("clientName") or attrs.get("client_name") or attrs.get("client"),
        policy=attrs.get("policyName") or attrs.get("policy_name") or attrs.get("policy"),
        policy_type=attrs.get("policyType") or attrs.get("policy_type"),
        schedule=attrs.get("scheduleName") or attrs.get("schedule_name") or attrs.get("schedule"),
        schedule_type=attrs.get("scheduleType") or attrs.get("schedule_type"),
        backup_time=attrs.get("backupTime") or attrs.get("backup_time"),
        expiration_time=attrs.get("expirationTime") or attrs.get("expiration_time"),
        retention_level=attrs.get("retentionLevel") or attrs.get("retention_level"),
        copy_number=attrs.get("copyNumber") or attrs.get("copy_number"),
        storage_location=attrs.get("storageLocation") or attrs.get("storage_location") or attrs.get("storage"),
        kilobytes=attrs.get("kilobytes") or attrs.get("kb"),
        raw=payload,
        source=source,
    )
