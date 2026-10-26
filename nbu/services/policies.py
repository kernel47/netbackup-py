from __future__ import annotations

from nbu.filters import combine, contains
from nbu.models.clients import Client
from nbu.models.policies import Policy
from nbu.models.slp import SLP, SLPDetails
from nbu.parsers.policies import (
    parse_policy_detail,
    parse_policy_summary,
    parse_protected_clients,
)
from nbu.parsers.slp import parse_slp
from nbu.services.base import ServiceBase


class PoliciesService(ServiceBase):
    def list(
        self,
        *,
        name: str | None = None,
        filter: str | None = None,
        limit: int | None = None,
        include_details: bool = False,
        resolve_slp: bool = False,
    ) -> list[Policy]:
        self.version.require("policies")
        if resolve_slp and not include_details:
            raise ValueError("resolve_slp requires include_details=True")
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
        cache: dict[str, SLP] = {}
        details = [self.get(policy.name) for policy in policies]
        if resolve_slp:
            for policy in details:
                self._resolve_slps(policy, cache)
        return details

    def get(self, policy_name: str, *, resolve_slp: bool = False) -> Policy:
        self.version.require("policies")
        api_version = self.config.service_api_version("config_policies")
        headers = {"Accept": f"application/vnd.netbackup+json;version={api_version}"}
        policy = parse_policy_detail(
            self.api.request(
                "GET",
                self.version.endpoint("policy", policy_name=policy_name),
                headers=headers,
            )
        )
        if resolve_slp:
            self._resolve_slps(policy, {})
        return policy

    def clients(
        self,
        *,
        name: str | None = None,
        filter: str | None = None,
        limit: int | None = None,
    ) -> list[Client]:
        self.version.require("policies")
        policies = self.list(name=name, filter=filter, limit=limit, include_details=True)
        return parse_protected_clients(policies)

    def _resolve_slps(self, policy: Policy, cache: dict[str, SLP]) -> None:
        names = {policy.slp} if policy.slp else set()
        for schedule in policy.schedules:
            if schedule.storage_is_slp is not True:
                continue
            # Read declared references from every copy, without adding derived fields.
            copies = (schedule.backup_copies or {}).get("copies", [])
            for copy in copies if isinstance(copies, list) else []:
                name = copy.get("storage") if isinstance(copy, dict) else None
                if isinstance(name, str) and name:
                    names.add(name)
        for name in sorted(names):
            if name not in cache:
                cache[name] = parse_slp(
                    self.api.request(
                        "GET",
                        self.version.endpoint("slp_detail", slp_name=name),
                        headers={
                            "Accept": "application/vnd.netbackup+json;version="
                            + self.config.service_api_version("config_slp")
                        },
                    )
                )
            policy.slps[name] = SLPDetails.model_validate(
                cache[name].model_dump(exclude={"raw", "source"})
            )
