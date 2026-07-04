from __future__ import annotations

from nbu.filters import combine, contains
from nbu.models.clients import Client, client_from_mapping
from nbu.services.base import ServiceBase


class ClientsService(ServiceBase):
    def list(
        self,
        *,
        name: str | None = None,
        filter: str | None = None,
        limit: int | None = None,
    ) -> list[Client]:
        self.version.require("clients")
        filter_value = combine(filter, contains("hostName", name) if name else None)
        params = self._drop_none({"filter": filter_value})
        return [
            client_from_mapping(item)
            for item in self.api.get_collection(self.version.endpoint("clients"), params, limit=limit)
        ]

    def get(self, client_name: str) -> Client:
        self.version.require("clients")
        return client_from_mapping(
            self.api.request("GET", self.version.endpoint("client", client_name=client_name))
        )
