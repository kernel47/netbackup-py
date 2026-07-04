from __future__ import annotations

from typing import Any

from nbu.models.base import NbuModel


class StorageUnit(NbuModel):
    name: str
    type: str | None = None
    media_server: str | None = None
    disk_pool: str | None = None
    capacity_bytes: int | None = None
    available_bytes: int | None = None
    status: str | None = None


class DiskPool(NbuModel):
    name: str
    type: str | None = None
    capacity_bytes: int | None = None
    available_bytes: int | None = None
    status: str | None = None


def storage_unit_from_mapping(payload: dict[str, Any], source: str = "api") -> StorageUnit:
    attrs = payload.get("attributes", payload)
    return StorageUnit(
        name=attrs.get("storageUnitName") or attrs.get("storage_unit") or attrs.get("name"),
        type=attrs.get("type"),
        media_server=attrs.get("mediaServer") or attrs.get("media_server"),
        disk_pool=attrs.get("diskPool") or attrs.get("disk_pool"),
        capacity_bytes=attrs.get("capacityBytes") or attrs.get("capacity_bytes"),
        available_bytes=attrs.get("availableBytes") or attrs.get("available_bytes"),
        status=attrs.get("status"),
        raw=payload,
        source=source,
    )


def disk_pool_from_mapping(payload: dict[str, Any], source: str = "api") -> DiskPool:
    attrs = payload.get("attributes", payload)
    return DiskPool(
        name=attrs.get("diskPoolName") or attrs.get("disk_pool") or attrs.get("name"),
        type=attrs.get("type"),
        capacity_bytes=attrs.get("capacityBytes") or attrs.get("capacity_bytes"),
        available_bytes=attrs.get("availableBytes") or attrs.get("available_bytes"),
        status=attrs.get("status"),
        raw=payload,
        source=source,
    )
