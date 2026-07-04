from __future__ import annotations

from nbu.config import CollectionMode
from nbu.models.vm import VMAsset, vm_asset_from_mapping
from nbu.services.base import ServiceBase


class VMService(ServiceBase):
    def assets(self, *, mode: CollectionMode | None = None) -> list[VMAsset]:
        if self._mode(mode) == "ssh":
            text = self.ssh.run("nbdiscover", "-noxmloutput")
            assets = []
            for line in text.splitlines():
                name = line.strip()
                if name:
                    assets.append(VMAsset(name=name, source="ssh", raw={"line": line}))
            return assets
        self.version.require("vmware_assets")
        return [
            vm_asset_from_mapping(item)
            for item in self.api.get_collection(self.version.endpoint("vmware_assets"))
        ]

