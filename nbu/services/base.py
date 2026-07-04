from __future__ import annotations

from typing import Any

from nbu.config import CollectionMode, NetBackupConfig
from nbu.transport.api import ApiTransport
from nbu.transport.ssh import SshTransport
from nbu.version import VersionManager


class ServiceBase:
    def __init__(
        self,
        config: NetBackupConfig,
        api: ApiTransport,
        ssh: SshTransport,
        version: VersionManager,
    ) -> None:
        self.config = config
        self.api = api
        self.ssh = ssh
        self.version = version
        self.client: object | None = None

    def attach_client(self, client: object) -> None:
        self.client = client

    def _mode(self, mode: CollectionMode | None) -> CollectionMode:
        return mode or self.config.mode

    @staticmethod
    def _drop_none(params: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in params.items() if value is not None}
