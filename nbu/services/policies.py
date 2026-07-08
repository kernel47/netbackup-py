from __future__ import annotations

from nbu.exceptions import NetBackupError
from nbu.filters import combine, contains
from nbu.models.clients import Client
from nbu.models.policies import Policy
from nbu.models.slp import SLP, SLPOperation
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
        headers = {"Accept": f"application/vnd.netbackup+json;version={api_version}"}
        policy = parse_policy_detail(
            self.api.request(
                "GET",
                self.version.endpoint("policy", policy_name=policy_name),
                headers=headers,
            )
        )
        self._enrich_slp(policy)
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

    def _get_slp(self, slp_name: str, cache: dict[str, SLP | None]) -> SLP | None:
        if slp_name not in cache:
            try:
                cache[slp_name] = parse_slp(
                    self.api.request("GET", self.version.endpoint("slp_detail", slp_name=slp_name))
                )
            except NetBackupError:
                cache[slp_name] = None
        return cache[slp_name]

    @staticmethod
    def _backup_operation(slp: SLP) -> SLPOperation | None:
        return next(
            (operation for operation in slp.operations if operation.operation.upper() == "BACKUP"),
            slp.operations[0] if slp.operations else None,
        )

    def _enrich_slp(self, policy: Policy) -> None:
        cache: dict[str, SLP | None] = {}
        if policy.storage_is_slp and policy.storage:
            slp = self._get_slp(policy.storage, cache)
            operation = self._backup_operation(slp) if slp else None
            if slp and slp.retention is not None:
                policy.retention = slp.retention
            if operation and operation.target_storage:
                policy.storage = operation.target_storage

        for schedule in policy.schedules:
            if not schedule.storage_is_slp or not schedule.storage:
                continue
            slp = self._get_slp(schedule.storage, cache)
            operation = self._backup_operation(slp) if slp else None
            if slp and slp.retention is not None:
                schedule.retention = slp.retention
            if operation and operation.target_storage:
                schedule.storage = operation.target_storage
