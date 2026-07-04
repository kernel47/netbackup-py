from __future__ import annotations

from nbu.config import CollectionMode
from nbu.models.clients import Client, client_from_mapping
from nbu.parsers import nbemmcmd
from nbu.services.base import ServiceBase


class ClientsService(ServiceBase):
    def list(self, *, mode: CollectionMode | None = None) -> list[Client]:
        if self._mode(mode) == "ssh":
            return nbemmcmd.parse_clients(self.ssh.run("nbemmcmd", "-listhosts"))
        self.version.require("clients")
        return [client_from_mapping(item) for item in self.api.get_collection(self.version.endpoint("clients"))]

    def get(self, client_name: str, *, mode: CollectionMode | None = None) -> Client:
        if self._mode(mode) == "ssh":
            for client in self.list(mode="ssh"):
                if client.name == client_name:
                    return client
            from nbu.exceptions import NotFoundError

            raise NotFoundError(f"Client {client_name!r} was not found")
        self.version.require("clients")
        return client_from_mapping(
            self.api.request("GET", self.version.endpoint("client", client_name=client_name))
        )

