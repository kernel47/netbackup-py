from __future__ import annotations

from nbu.filters import combine, contains
from nbu.models.storage import DiskPool, StorageUnit, disk_pool_from_mapping, storage_unit_from_mapping
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
            storage_unit_from_mapping(item)
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
            disk_pool_from_mapping(item)
            for item in self.api.get_collection(self.version.endpoint("disk_pools"), params, limit=limit)
        ]
