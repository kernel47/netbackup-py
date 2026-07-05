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


def test_discover_vmware_policy_clients_uses_workload_test_query() -> None:
    seen: dict[str, object] = {"result_gets": 0}

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

        if request.url.path == "/netbackup/config/workloads/vmware/test-query":
            seen["post_json"] = request.read().decode()
            return httpx.Response(
                200,
                json={
                    "data": {
                        "id": "query-1",
                        "attributes": {"testQueryId": "query-1", "isDiscoveryDone": True},
                    }
                },
            )

        seen["result_path"] = request.url.path
        seen["result_gets"] = int(seen["result_gets"]) + 1
        return httpx.Response(
            200,
            json={
                "data": {
                    "id": "query-1",
                    "attributes": {
                        "testQueryId": "query-1",
                        "isDiscoveryDone": True,
                        "discoveredAssets": [
                            {"id": "vm-1", "attributes": {"displayName": "app01"}},
                            {"id": "vm-2", "attributes": {"vmName": "app02"}},
                        ],
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

    clients = nb.discover_vmware_policy_clients("vmware-prod", poll_interval=0)

    assert '"type":"intelligentTestQueryRequest"' in str(seen["post_json"])
    assert '"testQuery":"vcenter Equal \\"vc01\\" and Tag NotEqual \\"no_backup\\""' in str(
        seen["post_json"]
    )
    assert seen["result_path"] == "/netbackup/config/workloads/vmware/test-query/query-1"
    assert [client.name for client in clients] == ["app01", "app02"]
    nb.close()


def test_discover_vmware_policy_clients_requires_vmware_selection() -> None:
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
        nb.discover_vmware_policy_clients("linux-prod")

    nb.close()
