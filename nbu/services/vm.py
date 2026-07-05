from __future__ import annotations

from nbu.exceptions import ApiError
from nbu.models.vm import VMwareClient, VMwareSelection
from nbu.parsers.vm import parse_preview_client, parse_vmware_selection
from nbu.services.base import ServiceBase


class VMService(ServiceBase):
    def policy_selections(self, policy_name: str) -> list[VMwareSelection]:
        policy = self._policy(policy_name)
        return [
            selection
            for raw in policy.backup_selections
            if (selection := parse_vmware_selection(raw)) is not None
        ]

    def preview_asset_group(self, query_filter: str, *, workload: str = "vmware") -> list[VMwareClient]:
        self.version.require("vmware_preview")
        data = self.api.request(
            "POST",
            self.version.endpoint("preview_asset_group"),
            json={
                "data": {
                    "type": workload,
                    "attributes": {"queryFilter": query_filter},
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
        items = data.get("data") or []
        if not isinstance(items, list):
            items = [items]
        return [parse_preview_client(item) for item in items if isinstance(item, dict)]

    def preview_policy_clients(
        self,
        policy_name: str,
        *,
        limit: int | None = None,
    ) -> list[VMwareClient]:
        selections = self.policy_selections(policy_name)
        if not selections:
            raise ApiError(f"Policy {policy_name!r} does not contain a VMware dynamic selection")

        clients: list[VMwareClient] = []
        seen: set[str] = set()
        for selection in selections:
            for client in self.preview_asset_group(selection.query_filter):
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
            raise ApiError("VMware policy preview requires a NetBackup client with PoliciesService attached")
        return self.client.policies.get(policy_name)
