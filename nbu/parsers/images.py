from __future__ import annotations

from typing import Any

from nbu.models.images import Image
from nbu.parsers.common import attributes, first_value, resource_id


def parse_image(payload: dict[str, Any], source: str = "api") -> Image:
    attrs = attributes(payload)
    image_id = (
        first_value(attrs, "imageId", "image_id", "id", "backupId", "backup_id")
        or resource_id(payload)
    )
    return Image(
        image_id=str(image_id or ""),
        backup_id=first_value(attrs, "backupId", "backup_id") or resource_id(payload),
        client=first_value(attrs, "clientName", "client_name", "client"),
        policy=first_value(attrs, "policyName", "policy_name", "policy"),
        policy_type=first_value(attrs, "policyType", "policy_type"),
        schedule=first_value(attrs, "scheduleName", "schedule_name", "schedule"),
        schedule_type=first_value(attrs, "scheduleType", "schedule_type"),
        backup_time=first_value(attrs, "backupTime", "backup_time"),
        expiration_time=first_value(attrs, "expirationTime", "expiration_time"),
        retention_level=first_value(attrs, "retentionLevel", "retention_level"),
        copy_number=first_value(attrs, "copyNumber", "copy_number"),
        storage_location=first_value(attrs, "storageLocation", "storage_location", "storage"),
        kilobytes=first_value(attrs, "kilobytes", "kb"),
        raw=payload,
        source=source,
    )
