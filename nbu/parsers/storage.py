from __future__ import annotations

from typing import Any

from nbu.models.storage import DiskPool, StorageUnit
from nbu.parsers.common import attributes, first_value, resource_id


def parse_storage_unit(payload: dict[str, Any], source: str = "api") -> StorageUnit:
    attrs = attributes(payload)
    return StorageUnit(
        name=first_value(attrs, "storageUnitName", "storage_unit", "name") or resource_id(payload),
        type=attrs.get("type"),
        media_server=first_value(attrs, "mediaServer", "media_server"),
        disk_pool=first_value(attrs, "diskPool", "disk_pool"),
        capacity_bytes=first_value(attrs, "capacityBytes", "capacity_bytes"),
        available_bytes=first_value(attrs, "availableBytes", "available_bytes"),
        status=attrs.get("status"),
        raw=payload,
        source=source,
    )


def parse_disk_pool(payload: dict[str, Any], source: str = "api") -> DiskPool:
    attrs = attributes(payload)
    return DiskPool(
        name=first_value(attrs, "diskPoolName", "disk_pool", "name") or resource_id(payload),
        type=attrs.get("type"),
        capacity_bytes=first_value(attrs, "capacityBytes", "capacity_bytes"),
        available_bytes=first_value(attrs, "availableBytes", "available_bytes"),
        status=attrs.get("status"),
        raw=payload,
        source=source,
    )
