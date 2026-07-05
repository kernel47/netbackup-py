from __future__ import annotations

from nbu.models.vm import VMAsset
from nbu.parsers.vm import parse_vm_asset
from nbu.services.base import ServiceBase


class VMService(ServiceBase):
    def assets(self, *, limit: int | None = None) -> list[VMAsset]:
        self.version.require("vmware_assets")
        return [
            parse_vm_asset(item)
            for item in self.api.get_collection(self.version.endpoint("vmware_assets"), limit=limit)
        ]
