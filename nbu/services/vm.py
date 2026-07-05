from __future__ import annotations

import time

from nbu.exceptions import ApiError
from nbu.models.vm import VMwareClient, VMwareSelection, VMwareTestQuery
from nbu.parsers.vm import parse_test_query, parse_test_query_clients, parse_vmware_selection
from nbu.services.base import ServiceBase


class VMService(ServiceBase):
    def policy_selections(self, policy_name: str) -> list[VMwareSelection]:
        policy = self._policy(policy_name)
        return [
            selection
            for raw in policy.backup_selections
            if (selection := parse_vmware_selection(raw)) is not None
        ]

    def start_test_query(self, query_filter: str, **attributes: object) -> VMwareTestQuery:
        self.version.require("vmware_test_query")
        data = self.api.request(
            "POST",
            self.version.endpoint("vmware_test_query"),
            json={
                "data": {
                    "type": "intelligentTestQueryRequest",
                    "attributes": {"testQuery": query_filter, **attributes},
                }
            },
            headers={
                "Accept": (
                    "application/vnd.netbackup+json;"
                    f"version={self.config.service_api_version('config')}"
                ),
                "Content-Type": (
                    "application/vnd.netbackup+json;"
                    f"version={self.config.service_api_version('config')}"
                ),
            },
        )
        return parse_test_query(data)

    def get_test_query(self, test_query_id: str) -> VMwareTestQuery:
        self.version.require("vmware_test_query")
        return parse_test_query(
            self.api.request(
                "GET",
                self.version.endpoint("vmware_test_query_result", test_query_id=test_query_id),
                headers={
                    "Accept": (
                        "application/vnd.netbackup+json;"
                        f"version={self.config.service_api_version('config')}"
                    )
                },
            )
        )

    def get_test_query_clients(self, test_query_id: str) -> list[VMwareClient]:
        self.version.require("vmware_test_query")
        data = self.api.request(
            "GET",
            self.version.endpoint("vmware_test_query_result", test_query_id=test_query_id),
            headers={
                "Accept": (
                    "application/vnd.netbackup+json;"
                    f"version={self.config.service_api_version('config')}"
                )
            },
        )
        return parse_test_query_clients(data)

    def discover_policy_clients(
        self,
        policy_name: str,
        *,
        limit: int | None = None,
        poll_interval: float = 2.0,
        timeout: float = 120.0,
        **test_query_attributes: object,
    ) -> list[VMwareClient]:
        selections = self.policy_selections(policy_name)
        if not selections:
            raise ApiError(f"Policy {policy_name!r} does not contain a VMware dynamic selection")

        clients: list[VMwareClient] = []
        seen: set[str] = set()
        for selection in selections:
            query = self.start_test_query(selection.query_filter, **test_query_attributes)
            deadline = time.monotonic() + timeout
            while query.done is not True and time.monotonic() < deadline:
                time.sleep(poll_interval)
                query = self.get_test_query(query.test_query_id)
            for client in self.get_test_query_clients(query.test_query_id):
                key = client.id or client.name
                if key in seen:
                    continue
                seen.add(key)
                clients.append(client)
                if limit is not None and len(clients) >= limit:
                    return clients
        return clients

    def _policy(self, policy_name: str):
        if self.client is None or not hasattr(self.client, "policies"):
            raise ApiError("VMware test-query requires a NetBackup client with PoliciesService attached")
        return self.client.policies.get(policy_name)
