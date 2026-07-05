import httpx
import pytest

from nbu import NetBackup, NetBackupConfig
from nbu.config import NetBackupConfig as DirectConfig
from nbu.exceptions import ApiError
from nbu.parsers.vm import parse_vmware_selection, vip_filter_to_odata
from nbu.services.vm import VMService
from nbu.transport.api import ApiTransport
from nbu.version import VersionManager


def test_vm_assets_use_asset_service_filter_and_offset_pagination() -> None:
    seen: list[tuple[str, str | None, str | None, str | None]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(
            (
                request.url.path,
                request.url.params.get("filter"),
                request.url.params.get("page[offset]"),
                request.headers.get("accept"),
            )
        )
        offset = request.url.params.get("page[offset]")
        if offset is None:
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": "vm-1",
                            "type": "vmwareAsset",
                            "attributes": {
                                "displayName": "app01",
                                "instanceUuid": "uuid-1",
                                "vcenter": "vc01",
                            },
                        }
                    ],
                    "meta": {"pagination": {"next": 1, "hasNext": True}},
                },
            )
        return httpx.Response(
            200,
            json={
                "data": [{"id": "vm-2", "attributes": {"displayName": "app02"}}],
                "meta": {"pagination": {"hasNext": False}},
            },
        )

    api = ApiTransport(
        DirectConfig(master="master.example.com", token="abc123", version="11.2"),
        transport=httpx.MockTransport(handler),
    )
    service = VMService(api.config, api, VersionManager("11.2"))

    assets = service.assets(filter="vcenter eq 'vc01'")

    assert [asset.name for asset in assets] == ["app01", "app02"]
    assert seen[0] == (
        "/netbackup/asset-service/workloads/vmware/assets",
        "vcenter eq 'vc01'",
        None,
        "application/vnd.netbackup+json;version=14.0",
    )
    assert seen[1][2] == "1"


def test_resolve_vmware_policy_assets_uses_policy_odata_filter() -> None:
    seen: dict[str, str | None] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/netbackup/config/policies/vmware-prod":
            seen["policy_header"] = request.headers.get("x-netbackup-include-vmware-odata-filter")
            return httpx.Response(
                200,
                json={
                    "data": {
                        "id": "vmware-prod",
                        "attributes": {
                            "policyVMware": {
                                "policyName": "vmware-prod",
                                "policyType": "VMware",
                                "backupSelections": [
                                    'vmware:/filter=vcenter Equal "vc01" and Tag NotEqual "no_backup"'
                                ],
                                "vmwareIntelligentClientSelections": [
                                    {"oDataFilter": "vcenter eq 'vc01' and tag ne 'no_backup'"}
                                ],
                            }
                        },
                    }
                },
            )

        seen["asset_path"] = request.url.path
        seen["asset_filter"] = request.url.params.get("filter")
        return httpx.Response(
            200,
            json={
                "data": [{"id": "vm-1", "attributes": {"displayName": "app01"}}],
                "meta": {"pagination": {"hasNext": False}},
            },
        )

    nb = NetBackup(
        config=NetBackupConfig(master="master.example.com", token="abc123", version="11.2"),
    )
    nb.api.close()
    nb.api = ApiTransport(nb.config, transport=httpx.MockTransport(handler))
    nb.policies.api = nb.api
    nb.vm.api = nb.api

    assets = nb.resolve_vmware_policy_assets("vmware-prod")

    assert seen["policy_header"] == "true"
    assert seen["asset_path"] == "/netbackup/asset-service/workloads/vmware/assets"
    assert seen["asset_filter"] == "vcenter eq 'vc01' and tag ne 'no_backup'"
    assert assets[0].name == "app01"
    nb.close()


def test_vmware_vip_filter_is_converted_to_odata() -> None:
    vip_filter = 'vcenter Equal "vc01" and cluster Contains "CL-prod" and Tag NotEqual "no_backup"'

    assert vip_filter_to_odata(vip_filter) == (
        "vcenter eq 'vc01' and contains(cluster,'CL-prod') and Tag ne 'no_backup'"
    )
    selection = parse_vmware_selection(f"vmware:/filter={vip_filter}")

    assert selection.filter == vip_filter
    assert selection.odata_filter == (
        "vcenter eq 'vc01' and contains(cluster,'CL-prod') and Tag ne 'no_backup'"
    )


def test_resolve_vmware_policy_assets_converts_backup_selection_when_odata_is_missing() -> None:
    seen: dict[str, str | None] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/netbackup/config/policies/vmware-prod":
            return httpx.Response(
                200,
                json={
                    "data": {
                        "id": "vmware-prod",
                        "attributes": {
                            "policyVMware": {
                                "policyName": "vmware-prod",
                                "policyType": "VMware",
                                "backupSelections": [
                                    'vmware:/filter=vcenter Equal "vc01" and cluster Contains "CL-prod"'
                                ],
                            }
                        },
                    }
                },
            )

        seen["asset_filter"] = request.url.params.get("filter")
        return httpx.Response(
            200,
            json={
                "data": [{"id": "vm-1", "attributes": {"displayName": "app01"}}],
                "meta": {"pagination": {"hasNext": False}},
            },
        )

    nb = NetBackup(
        config=NetBackupConfig(master="master.example.com", token="abc123", version="11.2"),
    )
    nb.api.close()
    nb.api = ApiTransport(nb.config, transport=httpx.MockTransport(handler))
    nb.policies.api = nb.api
    nb.vm.api = nb.api

    assets = nb.resolve_vmware_policy_assets("vmware-prod")

    assert seen["asset_filter"] == "vcenter eq 'vc01' and contains(cluster,'CL-prod')"
    assert assets[0].name == "app01"
    nb.close()


def test_resolve_vmware_policy_assets_requires_backup_selection_source() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": {
                    "id": "not-vmware-prod",
                    "attributes": {
                        "policyStandard": {
                            "policyName": "not-vmware-prod",
                            "policyType": "Standard",
                            "backupSelections": ["/var"],
                            "vmwareIntelligentClientSelections": [
                                {"oDataFilter": "vcenter eq 'vc01'"}
                            ],
                        }
                    },
                }
            },
        )

    nb = NetBackup(
        config=NetBackupConfig(master="master.example.com", token="abc123", version="11.2"),
    )
    nb.api.close()
    nb.api = ApiTransport(nb.config, transport=httpx.MockTransport(handler))
    nb.policies.api = nb.api
    nb.vm.api = nb.api

    with pytest.raises(ApiError, match="does not contain a VMware dynamic selection"):
        nb.resolve_vmware_policy_assets("not-vmware-prod")

    nb.close()
