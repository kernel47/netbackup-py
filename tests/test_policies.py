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
    assert policy.schedules[0].schedule_name == "full"
    assert policy.schedules[0].backup_type == "Full Backup"
    assert policy.backup_selections == ["/var"]


def test_policy_detail_parser_flattens_backup_selection_objects() -> None:
    policy = parse_policy_detail(
        {
            "data": {
                "id": "mixed-prod",
                "attributes": {
                    "policyStandard": {
                        "policyName": "mixed-prod",
                        "policyType": "Standard",
                        "backupSelections": [
                            {"selections": ["/etc", "/var"]},
                            {"selection": "/opt"},
                            'vmware:/filter=vcenter Equal "vc01"',
                        ],
                    }
                },
            }
        }
    )

    assert policy.backup_selections == [
        "/etc",
        "/var",
        "/opt",
        'vmware:/filter=vcenter Equal "vc01"',
    ]


def test_policy_detail_parser_handles_policy_shape_with_schedule_windows() -> None:
    policy = parse_policy_detail(
        {
            "data": {
                "type": "policy",
                "id": "linux-prod",
                "attributes": {
                    "policyStandard": {
                        "policyName": "linux-prod",
                        "policyType": "Standard",
                        "policyAttributes": {
                            "active": True,
                            "storage": "gold-slp",
                            "storageIsSLP": True,
                            "volumePool": "NetBackup",
                        },
                        "schedules": [
                            {
                                "backupType": "Cumulative Incremental Backup",
                                "storageIsSLP": True,
                                "backupCopies": {
                                    "copies": [
                                        {
                                            "retentionLevel": 2,
                                            "retentionPeriod": {"value": 14, "unit": "DAYS"},
                                            "storage": "silver-slp",
                                            "volumePool": "NetBackup",
                                        }
                                    ],
                                    "priority": 0,
                                },
                                "excludeDates": {"specificDates": ["2026-07-14"]},
                                "frequencySeconds": 3600,
                                "includeDates": {"recurringDaysOfWeek": ["MONDAY"]},
                                "scheduleName": "incr",
                                "scheduleType": "Calendar",
                                "startWindow": [
                                    {
                                        "durationSeconds": 7200,
                                        "startSeconds": 3600,
                                        "dayOfWeek": 1,
                                    }
                                ],
                            }
                        ],
                        "clients": [
                            {"hostName": "app01", "OS": "linux", "hardware": "x86"},
                            {"hostName": "app02"},
                        ],
                        "backupSelections": {"selections": ["/data", "/logs"]},
                    }
                },
            }
        }
    )

    assert policy.name == "linux-prod"
    assert policy.policy_type == "Standard"
    assert policy.active is True
    assert policy.clients == ["app01", "app02"]
    assert policy.backup_selections == ["/data", "/logs"]
    assert policy.storage == "gold-slp"
    assert policy.storage_is_slp is True

    schedule = policy.schedules[0]
    assert schedule.schedule_name == "incr"
    assert schedule.schedule_type == "Calendar"
    assert schedule.backup_type == "Cumulative Incremental Backup"
    assert schedule.retention == "14 DAYS"
    assert schedule.backup_copies == {
        "storage": "silver-slp",
        "retentionPeriod": "14 DAYS",
        "retentionLevel": 2,
        "volumePool": "NetBackup",
    }
    assert schedule.include_dates == {"recurringDaysOfWeek": ["MONDAY"]}
    assert schedule.exclude_dates == {"specificDates": ["2026-07-14"]}
    assert schedule.start_window == [
        {"durationSeconds": 7200, "startSeconds": 3600, "dayOfWeek": 1}
    ]
    assert schedule.storage == "silver-slp"
    assert schedule.storage_is_slp is True
    assert schedule.slp == "silver-slp"


def test_policy_parser_tolerates_missing_fields() -> None:
    policy = parse_policy_detail({"data": {"attributes": {"policyStandard": {}}}})

    assert policy.name == ""
    assert policy.clients == []
    assert policy.schedules == []
    assert policy.backup_selections == []


def test_policy_service_enriches_policy_and_schedule_from_slp() -> None:
    seen_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(request.url.path)
        if request.url.path == "/netbackup/config/policies/linux-prod":
            return httpx.Response(
                200,
                json={
                    "data": {
                        "id": "linux-prod",
                        "attributes": {
                            "policyStandard": {
                                "policyName": "linux-prod",
                                "policyType": "Standard",
                                "policyAttributes": {
                                    "storage": "policy-slp",
                                    "storageIsSLP": True,
                                },
                                "schedules": [
                                    {
                                        "scheduleName": "full",
                                        "scheduleType": "Calendar",
                                        "storageIsSLP": True,
                                        "backupCopies": {
                                            "copies": [{"storage": "schedule-slp"}]
                                        },
                                    }
                                ],
                                "clients": [{"hostName": "app01"}],
                            }
                        },
                    }
                },
            )
        slp_name = request.url.path.rsplit("/", 1)[-1]
        return httpx.Response(
            200,
            json={
                "data": {
                    "type": "slp",
                    "id": slp_name,
                    "attributes": {
                        "slpName": slp_name,
                        "active": True,
                        "operationList": [
                            {
                                "operationType": "BACKUP",
                                "retentionPeriod": {"value": 7, "unit": "DAYS"},
                                "retentionType": "FIXED",
                                "storage": {"name": f"{slp_name}-storage", "stype": "disk"},
                            }
                        ],
                    },
                }
            },
        )

    api = ApiTransport(
        NetBackupConfig(master="master.example.com", token="abc123", version="10.0"),
        transport=httpx.MockTransport(handler),
    )
    service = PoliciesService(api.config, api, VersionManager("10.0"))

    policy = service.get("linux-prod")

    assert policy.retention == "7 DAYS"
    assert policy.storage == "policy-slp-storage"
    assert policy.slp == "policy-slp"
    assert policy.schedules[0].retention == "7 DAYS"
    assert policy.schedules[0].storage == "schedule-slp-storage"
    assert policy.schedules[0].slp == "schedule-slp"
    assert seen_paths == [
        "/netbackup/config/policies/linux-prod",
        "/netbackup/config/slps/policy-slp",
        "/netbackup/config/slps/schedule-slp",
    ]
