import httpx
import pytest

from nbu import NetBackup, NetBackupConfig
from nbu.exceptions import ApiError
from nbu.parsers.vm import parse_vmware_selection
from nbu.transport.api import ApiTransport


def test_vmware_selection_is_read_from_backup_selection() -> None:
    selection = parse_vmware_selection(
        'vmware:/filter=vcenter Equal "vc01" and cluster Contains "CL-prod"'
    )

    assert selection is not None
    assert selection.query_filter == 'vcenter Equal "vc01" and cluster Contains "CL-prod"'


def test_preview_vmware_policy_clients_posts_preview_asset_group() -> None:
    seen: dict[str, object] = {}

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
                                    'vmware:/filter=vcenter Equal "vc01" and Tag NotEqual "no_backup"'
                                ],
                            }
                        },
                    }
                },
            )

        seen["path"] = request.url.path
        seen["json"] = request.read().decode()
        return httpx.Response(
            200,
            json={
                "data": [
                    {"id": "vm-1", "attributes": {"displayName": "app01"}},
                    {"id": "vm-2", "attributes": {"vmName": "app02"}},
                ]
            },
        )

    nb = NetBackup(
        config=NetBackupConfig(master="master.example.com", token="abc123", version="11.2"),
    )
    nb.api.close()
    nb.api = ApiTransport(nb.config, transport=httpx.MockTransport(handler))
    nb.policies.api = nb.api
    nb.vm.api = nb.api

    clients = nb.preview_vmware_policy_clients("vmware-prod")

    assert seen["path"] == "/netbackup/config/preview-asset-group"
    assert '"type":"vmware"' in str(seen["json"])
    assert 'vcenter Equal \\"vc01\\" and Tag NotEqual \\"no_backup\\"' in str(seen["json"])
    assert [client.name for client in clients] == ["app01", "app02"]
    nb.close()


def test_preview_vmware_policy_clients_requires_vmware_selection() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": {
                    "id": "linux-prod",
                    "attributes": {
                        "policyStandard": {
                            "policyName": "linux-prod",
                            "policyType": "Standard",
                            "backupSelections": ["/var"],
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
        nb.preview_vmware_policy_clients("linux-prod")

    nb.close()
