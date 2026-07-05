from __future__ import annotations

from nbu.filters import combine, contains
from nbu.models.storage import DiskPool, StorageUnit
from nbu.parsers.storage import parse_disk_pool, parse_storage_unit
from nbu.services.base import ServiceBase


class StorageService(ServiceBase):
    def storage_units(
        self,
        *,
        name: str | None = None,
        filter: str | None = None,
        limit: int | None = None,
    ) -> list[StorageUnit]:
        self.version.require("storage")
        filter_value = combine(filter, contains("name", name) if name else None)
        params = self._drop_none({"filter": filter_value})
        return [
            parse_storage_unit(item)
            for item in self.api.get_collection(self.version.endpoint("storage_units"), params, limit=limit)
        ]

    def disk_pools(
        self,
        *,
        name: str | None = None,
        filter: str | None = None,
        limit: int | None = None,
    ) -> list[DiskPool]:
        self.version.require("storage")
        filter_value = combine(filter, contains("name", name) if name else None)
        params = self._drop_none({"filter": filter_value})
        return [
            parse_disk_pool(item)
            for item in self.api.get_collection(self.version.endpoint("disk_pools"), params, limit=limit)
        ]
