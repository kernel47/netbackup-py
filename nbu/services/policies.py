from __future__ import annotations

from nbu.filters import combine, contains
from nbu.models.policies import Policy, policy_from_mapping
from nbu.services.base import ServiceBase


class PoliciesService(ServiceBase):
    def list(
        self,
        *,
        name: str | None = None,
        filter: str | None = None,
        limit: int | None = None,
    ) -> list[Policy]:
        self.version.require("policies")
        filter_value = combine(filter, contains("policyName", name) if name else None)
        params = self._drop_none({"filter": filter_value})
        return [
            policy_from_mapping(item)
            for item in self.api.get_collection(self.version.endpoint("policies"), params, limit=limit)
        ]

    def get(self, policy_name: str) -> Policy:
        self.version.require("policies")
        return policy_from_mapping(
            self.api.request("GET", self.version.endpoint("policy", policy_name=policy_name))
        )
