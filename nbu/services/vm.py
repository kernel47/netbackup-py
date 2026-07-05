from __future__ import annotations

from typing import Any

from nbu.exceptions import ApiError
from nbu.models.vm import VMAsset, VMwareSelection
from nbu.parsers.vm import VMWARE_SELECTION_PREFIX, parse_vm_asset, parse_vmware_selection
from nbu.services.base import ServiceBase


class VMService(ServiceBase):
    def workloads(self, *, include_details: bool = False, limit: int | None = None) -> list[dict[str, Any]]:
        self.version.require("vmware_assets")
        params = {"include": "workloadDetails"} if include_details else None
        return self.api.get_collection(
            self.version.endpoint("asset_workloads"),
            params,
            limit=limit,
            api_version=self.config.service_api_version("asset_service"),
        )

    def schemas(
        self,
        *,
        workload: str = "vmware",
        filter: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        self.version.require("vmware_assets")
        return self.api.get_collection(
            self.version.endpoint("asset_workload_schemas", workload=workload),
            self._drop_none({"filter": filter}),
            limit=limit,
            api_version=self.config.service_api_version("asset_service"),
        )

    def assets(
        self,
        *,
        workload: str = "vmware",
        filter: str | None = None,
        fields: list[str] | str | None = None,
        sort: str | None = None,
        meta: str | None = None,
        no_cache: bool = False,
        paginate: bool = True,
        limit: int | None = None,
    ) -> list[VMAsset]:
        self.version.require("vmware_assets")
        params = self._asset_params(filter=filter, fields=fields, sort=sort, meta=meta)
        headers = {"Cache-Control": "no-cache"} if no_cache else None
        return [
            parse_vm_asset(item)
            for item in self.api.get_collection(
                self.version.endpoint("asset_workload_assets", workload=workload),
                params,
                paginate=paginate,
                limit=limit,
                api_version=self.config.service_api_version("asset_service"),
                headers=headers,
            )
        ]

    def get_asset(self, asset_id: str, *, workload: str = "vmware", meta: str | None = None) -> VMAsset:
        self.version.require("vmware_assets")
        return parse_vm_asset(
            self.api.request(
                "GET",
                self.version.endpoint("asset_workload_asset", workload=workload, asset_id=asset_id),
                params=self._drop_none({"meta": meta}),
                headers={
                    "Accept": (
                        "application/vnd.netbackup+json;"
                        f"version={self.config.service_api_version('asset_service')}"
                    )
                },
            )
        )

    def policy_selections(self, policy_name: str) -> list[VMwareSelection]:
        policy = self._policy_with_vmware_odata(policy_name)
        raw_selections = self._vmware_backup_selections(policy.backup_selections)
        odata_filters = policy.vmware_odata_filters
        return [
            parse_vmware_selection(
                raw,
                odata_filter=odata_filters[index] if index < len(odata_filters) else None,
            )
            for index, raw in enumerate(raw_selections)
        ]

    def resolve_policy_assets(
        self,
        policy_name: str,
        *,
        workload: str = "vmware",
        filter: str | None = None,
        limit: int | None = None,
        no_cache: bool = False,
    ) -> list[VMAsset]:
        asset_filter = filter or self._policy_odata_filter(policy_name)
        return self.assets(workload=workload, filter=asset_filter, limit=limit, no_cache=no_cache)

    def _policy_with_vmware_odata(self, policy_name: str):
        if self.client is None or not hasattr(self.client, "policies"):
            raise ApiError("VMware policy resolution requires a NetBackup client with PoliciesService attached")
        return self.client.policies.get(policy_name, include_vmware_odata_filter=True)

    def _policy_odata_filter(self, policy_name: str) -> str:
        selections = self.policy_selections(policy_name)
        if not selections:
            raise ApiError(f"Policy {policy_name!r} does not contain a VMware dynamic selection")
        first_selection = selections[0]
        if not first_selection.odata_filter:
            raise ApiError(
                "Policy contains a VMware VIP query in backupSelections but it could not be converted "
                "to an Asset Service OData filter. Pass filter=... explicitly."
            )
        return first_selection.odata_filter

    @staticmethod
    def _vmware_backup_selections(backup_selections: list[str]) -> list[str]:
        return [
            selection
            for selection in backup_selections
            if selection.startswith(VMWARE_SELECTION_PREFIX)
        ]

    @staticmethod
    def _asset_params(
        *,
        filter: str | None = None,
        fields: list[str] | str | None = None,
        sort: str | None = None,
        meta: str | None = None,
    ) -> dict[str, Any]:
        if isinstance(fields, list):
            fields = ",".join(fields)
        return ServiceBase._drop_none(
            {"filter": filter, "fields[asset]": fields, "sort": sort, "meta": meta}
        )
