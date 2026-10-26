"""Regression cases based on SORT policies/configuration contracts 7.0–14.0.

See POLICY_PARSER_REVIEW.md for the official schema URLs. No server is needed.
"""

from copy import deepcopy

import httpx
import pytest

from nbu.config import NetBackupConfig
from nbu.exceptions import NotFoundError
from nbu.filters import combine
from nbu.parsers.images import parse_image
from nbu.parsers.jobs import parse_job
from nbu.parsers.policies import parse_policy_detail, parse_policy_summary, parse_schedule
from nbu.parsers.slp import parse_slp
from nbu.services.policies import PoliciesService
from nbu.services.slp import SLPService
from nbu.transport.api import ApiTransport
from nbu.version import VersionManager


@pytest.mark.parametrize(
    "envelope",
    [
        "policy",
        "policyStandard",
        "policyVMware",
        "policyOracle",
        "policyGeneric",
        "policyOLVMRHV",
        None,
    ],
)
def test_policy_preserves_all_configuration(envelope):
    body = {
        "policyName": "prod",
        "policyType": "Standard",
        "policyAttributes": {
            "active": False,
            "storage": "gold",
            "storageIsSLP": True,
            "priority": 0,
            "futureOption": {"enabled": False},
        },
        "clients": [{"hostName": "db", "OS": "linux", "instanceName": "db1", "clientId": "42"}],
        "backupSelections": {"selections": ["/data"], "futureFlag": False},
        "excludeSelections": {"selections": ["/tmp"]},
        "schedules": [
            {
                "scheduleName": "full",
                "storageIsSLP": False,
                "backupCopies": {
                    "copies": [
                        {"storage": None, "retentionLevel": 0},
                        {"storage": "tape", "retentionLevel": 9},
                    ],
                    "priority": 0,
                },
                "includeDates": {"lastDayOfMonth": False, "specificDates": []},
                "syntheticBackup": False,
                "mediaMultiplexing": 1,
                "futureOption": {"value": 0},
            }
        ],
    }
    payload = {
        "data": {
            "id": "prod",
            "type": "policy",
            "attributes": {envelope: body} if envelope else body,
        }
    }
    original = deepcopy(payload)
    policy = parse_policy_detail(payload)
    assert policy.clients == ["db"]
    assert not hasattr(policy, "configuration")
    assert not hasattr(policy, "client_details")
    assert not hasattr(policy, "policy_attributes")
    schedule = policy.schedules[0]
    assert schedule.backup_copies == body["schedules"][0]["backupCopies"]
    assert schedule.include_dates == {"lastDayOfMonth": False, "specificDates": []}
    assert set(schedule.model_dump()) == {
        "schedule_name",
        "schedule_type",
        "backup_type",
        "frequency_seconds",
        "start_window",
        "include_dates",
        "exclude_dates",
        "storage_is_slp",
        "backup_copies",
    }
    assert policy.raw == original
    assert not hasattr(schedule, "raw")
    payload.clear()
    schedule.backup_copies["copies"][0]["storage"] = "edited"
    exported = policy.model_dump()
    exported["raw"]["data"]["attributes"].clear()
    assert policy.raw == original  # inputs, model views and exports are independent


def test_summary_reads_top_level_slp_flag():
    policy = parse_policy_summary(
        {
            "id": "prod",
            "type": "Standard",
            "attributes": {"storage": "gold", "storageIsSLP": True, "active": False},
        }
    )
    assert (policy.storage, policy.storage_is_slp, policy.slp) == ("gold", True, "gold")
    assert policy.active is False


@pytest.mark.parametrize("backup_copies", [None, {}, {"copies": []}])
def test_empty_copies_do_not_crash_or_invent_values(backup_copies):
    payload = {"scheduleName": "full"}
    if backup_copies is not None:
        payload["backupCopies"] = backup_copies
    schedule = parse_schedule(payload)
    assert schedule.backup_copies == backup_copies
    assert not hasattr(schedule, "raw")


@pytest.mark.parametrize(
    "period", [{"value": 0, "unit": "DAYS"}, {"value": -1, "unit": "DAYS"}, {"unit": "INFINITE"}]
)
def test_structured_retention_is_not_rewritten(period):
    schedule = parse_schedule({"backupCopies": {"copies": [{"retentionPeriod": period}]}})
    assert schedule.backup_copies == {"copies": [{"retentionPeriod": period}]}


def test_slp_has_no_arbitrary_global_retention_or_destination():
    payload = {
        "data": {
            "id": "gold",
            "attributes": {
                "slpName": "gold",
                "versionNumber": 8,
                "active": False,
                "flagValues": ["inactive"],
                "operationList": [
                    {
                        "operationType": "SNAPSHOT",
                        "operationIndex": 1,
                        "sourceOperationIndex": 0,
                        "retentionType": "MAXIMUM_SNAPSHOT_LIMIT",
                        "storage": {"name": "snap"},
                        "retentionPeriod": {"value": 0, "unit": "DAYS"},
                    },
                    {
                        "operationType": "DUPLICATION",
                        "operationIndex": 2,
                        "sourceOperationIndex": 1,
                        "retentionType": "FIXED",
                        "storage": {"name": "tape"},
                        "retentionPeriod": {"value": -1, "unit": "INFINITE"},
                        "futureField": False,
                    },
                ],
            },
        }
    }
    slp = parse_slp(payload)
    assert slp.version_number == 8
    assert slp.retention is None
    assert slp.target_storage is None
    assert slp.operations[1].retention == {"value": -1, "unit": "INFINITE"}
    assert slp.operations[1].source_operation_index == 1
    assert slp.raw == payload
    assert slp.raw["data"]["attributes"]["operationList"][1]["futureField"] is False
    assert not hasattr(slp.operations[1], "raw")


def make_service(handler, **config):
    api = ApiTransport(
        NetBackupConfig(master="m", token="t", version="11.1", **config),
        transport=httpx.MockTransport(handler),
    )
    return PoliciesService(api.config, api, VersionManager("11.1"))


def test_default_get_never_reads_slp_and_explicit_resolution_propagates_errors():
    paths = []
    payload = {
        "data": {
            "attributes": {
                "policyStandard": {
                    "policyName": "p",
                    "policyAttributes": {"storage": "gold", "storageIsSLP": True},
                }
            }
        }
    }

    def handler(request):
        paths.append(request.url.path)
        if request.url.path.endswith("/p"):
            return httpx.Response(200, json=payload)
        return httpx.Response(404)

    service = make_service(handler)
    assert service.get("p").raw == payload
    assert paths == ["/netbackup/config/policies/p"]
    with pytest.raises(NotFoundError):
        service.get("p", resolve_slp=True)


def test_list_resolution_shares_cache_and_respects_service_versions():
    slp_calls = []

    def handler(request):
        path = request.url.path
        if "/slps/" in path:
            slp_calls.append(path)
            assert request.headers["accept"].endswith("version=13.0")
            return httpx.Response(
                200, json={"data": {"attributes": {"slpName": "gold", "versionNumber": 2}}}
            )
        assert request.headers["accept"].endswith("version=14.0")
        if path.endswith("/policies/"):
            return httpx.Response(
                200,
                json={
                    "data": [{"id": "a"}, {"id": "b"}],
                    "meta": {"pagination": {"hasNext": False}},
                },
            )
        return httpx.Response(
            200,
            json={
                "data": {
                    "id": path.rsplit("/", 1)[-1],
                    "attributes": {
                        "policyStandard": {
                            "policyAttributes": {"storage": "gold", "storageIsSLP": True}
                        }
                    },
                }
            },
        )

    service = make_service(handler, api_versions={"config_slp": "13.0"})
    policies = service.list(include_details=True, resolve_slp=True)
    assert slp_calls == ["/netbackup/config/slps/gold"]
    assert [p.storage for p in policies] == ["gold", "gold"]
    policies[0].slps["gold"].version_number = 999
    assert policies[1].slps["gold"].version_number == 2
    SLPService(service.config, service.api, service.version).get("gold")
    assert len(slp_calls) == 2


@pytest.mark.parametrize(
    "version, expected",
    [
        ("10.0", "7.0"),
        ("10.1", "8.0"),
        ("10.1.1", "9.0"),
        ("10.1.1.1", "9.0"),
        ("10.2", "9.0"),
        ("10.3", "10.0"),
        ("10.4", "11.0"),
        ("10.5", "12.0"),
        ("11.0", "13.0"),
        ("11.1", "14.0"),
        ("11.2", "14.0"),
    ],
)
def test_api_contract_versions(version, expected):
    config = NetBackupConfig(master="m", version=version)
    assert config.api_version == expected
    assert config.service_api_version("config_policies") == expected


def test_unknown_release_requires_explicit_contract():
    with pytest.raises(ValueError, match="api_version"):
        NetBackupConfig(master="m", version="12.0")
    assert NetBackupConfig(master="m", version="12.0", api_version="14.0").api_version == "14.0"
    config = NetBackupConfig(
        master="m", version="11.1", api_version="13.0", api_versions={"config_policies": "12.0"}
    )
    assert config.service_api_version("config_policies") == "12.0"


def test_offset_lookahead_follows_encoded_links_and_stops_on_false():
    offsets = []

    def handler(request):
        offset = request.url.params.get("page[offset]")
        offsets.append(offset)
        if offset is None:
            return httpx.Response(
                200,
                json={
                    "data": [{"id": "a"}],
                    "links": {"next": {"href": "/config/policies/?page%5Boffset%5D=1"}},
                    "meta": {"pagination": {"hasNext": True, "offset": 0, "limit": 1}},
                },
            )
        return httpx.Response(
            200,
            json={
                "data": [{"id": "b"}],
                "links": {"next": {"href": "/config/policies/?page%5Boffset%5D=2"}},
                "meta": {"pagination": {"hasNext": False}},
            },
        )

    service = make_service(handler)
    assert [p.name for p in service.list()] == ["a", "b"]
    assert offsets == [None, "1"]
    assert (
        ApiTransport._next_offset(
            {"meta": {"pagination": {"hasNext": True, "offset": 10, "limit": 5}}}
        )
        == "15"
    )
    assert (
        ApiTransport._next_offset(
            {"links": {"next": "/admin/jobs?page%5Bafter%5D=abc%2Bdef%3D"}}, pagination="cursor"
        )
        == "abc+def="
    )
    assert ApiTransport._total_count({"meta": {"pagination": {"count": 10}}}) is None


def test_filters_keep_custom_or_grouped():
    assert combine("status eq 0 or status eq 1", "clientName eq 'a'") == (
        "(status eq 0 or status eq 1) and (clientName eq 'a')"
    )


@pytest.mark.parametrize("parser", [parse_job, parse_image])
def test_other_parsers_preserve_unknown_fields_and_isolate_exports(parser):
    payload = {"data": {"id": "1", "attributes": {"unknown": {"enabled": False}}}}
    parsed = parser(payload)
    assert parsed.raw == payload
    exported = parsed.model_dump()
    exported["raw"]["data"]["attributes"]["unknown"]["enabled"] = True
    assert parsed.raw == payload
    assert not hasattr(parsed, "to_api")
    assert not hasattr(parsed, "api_attributes")
