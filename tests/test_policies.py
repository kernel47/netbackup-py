import httpx

from nbu.config import NetBackupConfig
from nbu.parsers.policies import parse_policy_detail
from nbu.services.policies import PoliciesService
from nbu.transport.api import ApiTransport
from nbu.version import VersionManager


def test_policy_list_keeps_summary_shape_without_clients() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/netbackup/config/policies/"
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "linux-prod",
                        "attributes": {
                            "policyName": "linux-prod",
                            "policyType": "STANDARD",
                            "active": True,
                        },
                    }
                ],
                "meta": {"pagination": {"hasNext": False}},
            },
        )

    api = ApiTransport(
        NetBackupConfig(master="master.example.com", token="abc123", version="10.0"),
        transport=httpx.MockTransport(handler),
    )
    service = PoliciesService(api.config, api, VersionManager("10.0"))

    policies = service.list()

    assert policies[0].name == "linux-prod"
    assert policies[0].clients == []


def test_policy_clients_are_built_from_policy_details() -> None:
    seen_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(request.url.path)
        if request.url.path == "/netbackup/config/unique-policy-clients":
            return httpx.Response(404, json={"error": "not found"})
        if request.url.path == "/netbackup/config/policies/":
            return httpx.Response(
                200,
                json={
                    "data": [
                        {"id": "linux-prod", "attributes": {"policyName": "linux-prod"}},
                        {"id": "db-prod", "attributes": {"policyName": "db-prod"}},
                    ],
                    "meta": {"pagination": {"hasNext": False}},
                },
            )
        policy_name = request.url.path.rsplit("/", 1)[-1]
        clients = {
            "linux-prod": ["app01", "app02"],
            "db-prod": ["app02", "db01"],
        }[policy_name]
        return httpx.Response(
            200,
            json={
                "data": {
                    "id": policy_name,
                    "attributes": {
                        "policyName": policy_name,
                        "policyType": "STANDARD",
                        "clients": clients,
                    },
                }
            },
        )

    api = ApiTransport(
        NetBackupConfig(master="master.example.com", token="abc123", version="10.0"),
        transport=httpx.MockTransport(handler),
    )
    service = PoliciesService(api.config, api, VersionManager("10.0"))

    clients = service.clients()

    assert [client.name for client in clients] == ["app01", "app02", "db01"]
    assert clients[1].policies == ["db-prod", "linux-prod"]
    assert seen_paths == [
        "/netbackup/config/unique-policy-clients",
        "/netbackup/config/policies/",
        "/netbackup/config/policies/linux-prod",
        "/netbackup/config/policies/db-prod",
    ]


def test_policy_clients_use_unique_policy_clients_endpoint() -> None:
    seen: dict[str, str | None] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["filter"] = request.url.params.get("filter")
        seen["accept"] = request.headers.get("accept")
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "app01",
                        "type": "uniqueClient",
                        "attributes": {
                            "hardware": "x86",
                            "OS": "linux",
                            "policyNames": ["linux-prod"],
                            "policyTypes": ["STANDARD"],
                        },
                    }
                ],
                "meta": {"pagination": {"hasNext": False}},
            },
        )

    api = ApiTransport(
        NetBackupConfig(master="master.example.com", token="abc123", version="11.2"),
        transport=httpx.MockTransport(handler),
    )
    service = PoliciesService(api.config, api, VersionManager("11.2"))

    clients = service.clients(name="app")

    assert seen["path"] == "/netbackup/config/unique-policy-clients"
    assert seen["filter"] == "contains(id,'app')"
    assert seen["accept"] == "application/vnd.netbackup+json;version=12.0"
    assert clients[0].name == "app01"
    assert clients[0].os == "linux"
    assert clients[0].policies == ["linux-prod"]


def test_policy_detail_parser_handles_nested_policy_schema_clients() -> None:
    policy = parse_policy_detail(
        {
            "data": {
                "id": "linux-prod",
                "attributes": {
                    "policyStandard": {
                        "policyName": "linux-prod",
                        "policyType": "Standard",
                        "clients": [
                            {"hostName": "app01", "osNameAndHardware": "redhat_x64"},
                            {"hostName": "app02", "osNameAndHardware": "aix_rs6000"},
                        ],
                        "schedules": [{"scheduleName": "full", "backupType": "Full Backup"}],
                        "backupSelections": ["/var"],
                    }
                },
            }
        }
    )

    assert policy.name == "linux-prod"
    assert policy.policy_type == "Standard"
    assert policy.clients == ["app01", "app02"]
    assert policy.schedules[0].name == "full"
    assert policy.backup_selections == ["/var"]


def test_policy_detail_parser_keeps_vmware_odata_filters() -> None:
    policy = parse_policy_detail(
        {
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
        }
    )

    assert policy.backup_selections == [
        'vmware:/filter=vcenter Equal "vc01" and Tag NotEqual "no_backup"'
    ]
    assert policy.vmware_odata_filters == ["vcenter eq 'vc01' and tag ne 'no_backup'"]
