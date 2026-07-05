from __future__ import annotations

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
