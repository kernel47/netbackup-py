from __future__ import annotations

from nbu.services.base import ServiceBase


class LicensingService(ServiceBase):
    def list(self) -> list[dict]:
        self.version.require("licensing")
        return self.api.get_collection(self.version.endpoint("licenses"))

