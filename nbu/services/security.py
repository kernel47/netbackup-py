from __future__ import annotations

from nbu.services.base import ServiceBase


class SecurityService(ServiceBase):
    def certificates(self) -> list[dict]:
        self.version.require("security")
        return self.api.get_collection(self.version.endpoint("certificates"))

