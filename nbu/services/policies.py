from __future__ import annotations

from nbu.exceptions import ApiError, NotFoundError
from nbu.filters import combine, contains
from nbu.models.clients import Client
from nbu.models.policies import Policy
from nbu.parsers.policies import (
    parse_policy_detail,
    parse_policy_summary,
    parse_protected_clients,
    parse_unique_policy_client,
)
from nbu.services.base import ServiceBase


class PoliciesService(ServiceBase):
    def list(
        self,
        *,
        name: str | None = None,
        filter: str | None = None,
        limit: int | None = None,
        include_details: bool = False,
    ) -> list[Policy]:
        self.version.require("policies")
        filter_value = combine(filter, contains("policyName", name) if name else None)
        params = self._drop_none({"filter": filter_value})
        api_version = self.config.service_api_version("config_policies")
        policies = [
            parse_policy_summary(item)
            for item in self.api.get_collection(
                self.version.endpoint("policies"),
                params,
                limit=limit,
                api_version=api_version,
            )
        ]
        if not include_details:
            return policies
        return [self.get(policy.name) for policy in policies]

    def get(self, policy_name: str) -> Policy:
        self.version.require("policies")
        api_version = self.config.service_api_version("config_policies")
        return parse_policy_detail(
            self.api.request(
                "GET",
                self.version.endpoint("policy", policy_name=policy_name),
                headers={"Accept": f"application/vnd.netbackup+json;version={api_version}"},
            )
        )

    def clients(
        self,
        *,
        name: str | None = None,
        filter: str | None = None,
        limit: int | None = None,
    ) -> list[Client]:
        self.version.require("policies")
        filter_value = combine(filter, contains("id", name) if name else None)
        params = self._drop_none({"filter": filter_value})
        api_version = self.config.service_api_version("config_policies")
        try:
            return [
                parse_unique_policy_client(item)
                for item in self.api.get_collection(
                    self.version.endpoint("unique_policy_clients"),
                    params,
                    limit=limit,
                    api_version=api_version,
                )
            ]
        except (ApiError, NotFoundError):
            pass
        policies = self.list(name=name, filter=filter, limit=limit, include_details=True)
        return parse_protected_clients(policies)
