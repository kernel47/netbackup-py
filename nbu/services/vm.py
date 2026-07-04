from __future__ import annotations

from nbu.models.vm import VMAsset, vm_asset_from_mapping
from nbu.services.base import ServiceBase


class VMService(ServiceBase):
    def assets(self, *, limit: int | None = None) -> list[VMAsset]:
        self.version.require("vmware_assets")
        return [
            vm_asset_from_mapping(item)
            for item in self.api.get_collection(self.version.endpoint("vmware_assets"), limit=limit)
        ]
