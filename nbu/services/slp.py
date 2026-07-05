from __future__ import annotations

from nbu.filters import combine, contains
from nbu.models.slp import SLP
from nbu.parsers.slp import parse_slp
from nbu.services.base import ServiceBase


class SLPService(ServiceBase):
    def list(
        self,
        *,
        name: str | None = None,
        filter: str | None = None,
        limit: int | None = None,
    ) -> list[SLP]:
        self.version.require("slp")
        filter_value = combine(filter, contains("slpName", name) if name else None)
        params = self._drop_none({"filter": filter_value})
        return [
            parse_slp(item)
            for item in self.api.get_collection(self.version.endpoint("slp"), params, limit=limit)
        ]

    def get(self, slp_name: str) -> SLP:
        self.version.require("slp")
        return parse_slp(self.api.request("GET", self.version.endpoint("slp_detail", slp_name=slp_name)))
