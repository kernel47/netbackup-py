from __future__ import annotations

from nbu.config import CollectionMode
from nbu.filters import contains
from nbu.models.policies import Policy, policy_from_mapping
from nbu.parsers import bppllist
from nbu.services.base import ServiceBase


class PoliciesService(ServiceBase):
    def list(self, *, mode: CollectionMode | None = None, name: str | None = None) -> list[Policy]:
        if self._mode(mode) == "ssh":
            return bppllist.parse(self.ssh.run("bppllist", "-allpolicies", "-U"))
        self.version.require("policies")
        params = self._drop_none({"filter": contains("policyName", name) if name else None})
        return [
            policy_from_mapping(item)
            for item in self.api.get_collection(self.version.endpoint("policies"), params)
        ]

    def get(self, policy_name: str, *, mode: CollectionMode | None = None) -> Policy:
        if self._mode(mode) == "ssh":
            for policy in self.list(mode="ssh"):
                if policy.name == policy_name:
                    return policy
            from nbu.exceptions import NotFoundError

            raise NotFoundError(f"Policy {policy_name!r} was not found")
        self.version.require("policies")
        return policy_from_mapping(
            self.api.request("GET", self.version.endpoint("policy", policy_name=policy_name))
        )
