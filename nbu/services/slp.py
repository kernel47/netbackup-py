from __future__ import annotations

from nbu.config import CollectionMode
from nbu.models.slp import SLP, slp_from_mapping
from nbu.parsers import nbstl
from nbu.services.base import ServiceBase


class SLPService(ServiceBase):
    def list(self, *, mode: CollectionMode | None = None) -> list[SLP]:
        if self._mode(mode) == "ssh":
            return nbstl.parse(self.ssh.run("nbstl", "-L"))
        self.version.require("slp")
        return [slp_from_mapping(item) for item in self.api.get_collection(self.version.endpoint("slp"))]

    def get(self, slp_name: str, *, mode: CollectionMode | None = None) -> SLP:
        if self._mode(mode) == "ssh":
            for slp in self.list(mode="ssh"):
                if slp.name == slp_name:
                    return slp
            from nbu.exceptions import NotFoundError

            raise NotFoundError(f"SLP {slp_name!r} was not found")
        self.version.require("slp")
        return slp_from_mapping(self.api.request("GET", self.version.endpoint("slp_detail", slp_name=slp_name)))

