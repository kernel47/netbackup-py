import httpx

from nbu.config import NetBackupConfig
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
        "/netbackup/config/policies/",
        "/netbackup/config/policies/linux-prod",
        "/netbackup/config/policies/db-prod",
    ]

