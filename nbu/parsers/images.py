from __future__ import annotations

from copy import deepcopy
from typing import Any

from nbu.models.images import Image
from nbu.parsers.common import attributes, first_present, resource_id


def parse_image(payload: dict[str, Any], source: str = "api") -> Image:
    attrs = deepcopy(attributes(payload))
    image_id = first_present(attrs, "imageId", "image_id", "id", "backupId", "backup_id")
    if image_id is None:
        image_id = resource_id(payload)
    backup_id = first_present(attrs, "backupId", "backup_id")
    if "backupId" not in attrs and "backup_id" not in attrs:
        backup_id = resource_id(payload)
    # A nested storage object is not a single image-wide storage location.
    storage = first_present(attrs, "storageLocation", "storage_location", "storage")
    return Image(
        image_id=str(image_id) if image_id is not None else "",
        backup_id=backup_id,
        client=first_present(attrs, "clientName", "client_name", "client"),
        policy=first_present(attrs, "policyName", "policy_name", "policy"),
        policy_type=first_present(attrs, "policyType", "policy_type"),
        schedule=first_present(attrs, "scheduleName", "schedule_name", "schedule"),
        schedule_type=first_present(attrs, "scheduleType", "schedule_type"),
        backup_time=first_present(attrs, "backupTime", "backup_time"),
        expiration_time=first_present(attrs, "expiration", "expirationTime", "expiration_time"),
        retention_level=first_present(attrs, "retentionLevel", "retention_level"),
        copy_number=first_present(attrs, "copyNumber", "copy_number"),
        storage_location=storage if isinstance(storage, str) else None,
        kilobytes=first_present(attrs, "kbytes", "kilobytes", "kb"),
        fragments=attrs.get("fragments") or [],
        num_copies=attrs.get("numCopies"),
        primary_copy=attrs.get("primaryCopy"),
        num_files=attrs.get("numFiles"),
        elapsed_seconds=attrs.get("elapsedTimeSeconds"),
        slp_name=attrs.get("slpName"),
        slp_version=attrs.get("slpVersion"),
        raw=payload,
        source=source,
    )
