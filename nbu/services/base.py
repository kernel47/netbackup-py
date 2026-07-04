from __future__ import annotations

from typing import Any

from nbu.config import NetBackupConfig
from nbu.transport.api import ApiTransport
from nbu.version import VersionManager


class ServiceBase:
    def __init__(
        self,
        config: NetBackupConfig,
        api: ApiTransport,
        version: VersionManager,
    ) -> None:
        self.config = config
        self.api = api
        self.version = version
        self.client: object | None = None

    def attach_client(self, client: object) -> None:
        self.client = client

    @staticmethod
    def _drop_none(params: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in params.items() if value is not None}
