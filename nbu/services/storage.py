from __future__ import annotations

from nbu.config import CollectionMode
from nbu.models.storage import DiskPool, StorageUnit, disk_pool_from_mapping, storage_unit_from_mapping
from nbu.parsers import bpstulist
from nbu.services.base import ServiceBase


class StorageService(ServiceBase):
    def storage_units(self, *, mode: CollectionMode | None = None) -> list[StorageUnit]:
        if self._mode(mode) == "ssh":
            return bpstulist.parse(self.ssh.run("bpstulist", "-U"))
        self.version.require("storage")
        return [
            storage_unit_from_mapping(item)
            for item in self.api.get_collection(self.version.endpoint("storage_units"))
        ]

    def disk_pools(self, *, mode: CollectionMode | None = None) -> list[DiskPool]:
        if self._mode(mode) == "ssh":
            return []
        self.version.require("storage")
        return [
            disk_pool_from_mapping(item)
            for item in self.api.get_collection(self.version.endpoint("disk_pools"))
        ]

