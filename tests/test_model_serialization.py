"""Keep one original response per resource and a predictable JSON interface."""

import json
from datetime import UTC, datetime

import pytest

from nbu.collectors.base import CollectionResult
from nbu.models.clients import Client
from nbu.models.images import Image
from nbu.models.jobs import Job
from nbu.models.policies import Policy
from nbu.models.slp import SLP
from nbu.parsers.policies import parse_policy_detail
from nbu.parsers.slp import parse_slp


@pytest.mark.parametrize(
    "model",
    [
        Job(start_time=datetime(2026, 10, 26, tzinfo=UTC)),
        Image(backup_time=datetime(2026, 10, 26, tzinfo=UTC)),
        Policy(),
        SLP(),
        Client(),
        CollectionResult(
            collector="jobs",
            records=[Job(end_time=datetime(2026, 10, 26, tzinfo=UTC))],
            metadata={"at": datetime(2026, 10, 26, tzinfo=UTC)},
        ),
    ],
)
def test_model_dump_supports_dictionary_and_json_text(model):
    dumped = model.model_dump()
    assert isinstance(dumped, dict)
    json_text = model.model_dump(mode="json", indent=2)
    assert isinstance(json_text, str)
    assert "\n  " in json_text
    assert isinstance(json.loads(json_text), dict)
    assert not hasattr(model, "model_dump_json")
    assert not hasattr(model, "to_api")
    assert not hasattr(model, "api_attributes")


def raw_paths(value, path=()):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "raw":
                yield path + (key,)
            else:
                yield from raw_paths(item, path + (key,))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from raw_paths(item, path + (index,))


def test_policy_has_one_raw_even_with_schedules_and_resolved_slps():
    payload = {
        "data": {
            "attributes": {
                "policyStandard": {
                    "policyName": "prod",
                    "policyAttributes": {"storage": "gold", "storageIsSLP": True},
                    "schedules": [
                        {
                            "scheduleName": "full",
                            "backupCopies": {"copies": []},
                            "futureField": {"enabled": False},
                        }
                    ],
                    "clients": [{"hostName": "db", "OS": "linux"}],
                }
            }
        }
    }
    policy = parse_policy_detail(payload)
    slp = parse_slp(
        {
            "data": {
                "attributes": {
                    "slpName": "gold",
                    "operationList": [
                        {"operationType": "BACKUP", "retentionPeriod": {"value": 7, "unit": "DAYS"}}
                    ],
                }
            }
        }
    )
    # Exercise the same conversion used by optional SLP resolution.
    from nbu.models.slp import SLPDetails

    policy.slps["gold"] = SLPDetails.model_validate(slp.model_dump(exclude={"raw", "source"}))
    dumped = policy.model_dump()
    assert list(raw_paths(dumped)) == [("raw",)]
    assert dumped["raw"] == payload
    assert set(dumped).isdisjoint({"configuration", "policy_attributes", "client_details"})
    assert policy.schedules[0].schedule_name == "full"
    assert json.loads(policy.model_dump(mode="json")) == dumped


def test_standalone_slp_has_one_raw_and_no_operation_raw():
    payload = {
        "data": {
            "attributes": {
                "slpName": "gold",
                "operationList": [{"operationType": "BACKUP", "futureField": {"enabled": False}}],
            }
        }
    }
    slp = parse_slp(payload)
    assert list(raw_paths(slp.model_dump())) == [("raw",)]
    assert slp.raw == payload


def test_dump_keeps_explicit_python_mode_and_standard_options():
    timestamp = datetime(2026, 10, 26, tzinfo=UTC)
    job = Job(id=7, start_time=timestamp)
    assert job.model_dump(mode="python")["start_time"] is timestamp
    assert job.model_dump(include={"job_id"}, by_alias=True) == {"id": 7}
    assert "raw" not in job.model_dump(exclude={"raw"})


def test_json_dump_keeps_filters_and_aliases():
    job = Job(id=7, start_time=datetime(2026, 10, 26, tzinfo=UTC))
    assert json.loads(job.model_dump(mode="json", indent=4, include={"job_id"}, by_alias=True)) == {
        "id": 7
    }
    assert json.loads(job.model_dump(mode="json", exclude={"raw"}))["start_time"].endswith("Z")
    with pytest.raises(ValueError, match="indent"):
        job.model_dump(indent=2)
    with pytest.raises(ValueError, match="mode"):
        job.model_dump(mode="invalid")


def test_indexable_records_stay_json_compatible_dictionaries():
    result = CollectionResult(
        collector="jobs", records=[Job(id=7, start_time=datetime(2026, 10, 26, tzinfo=UTC))]
    )
    records = result.to_indexable()
    assert isinstance(records[0], dict)
    assert records[0]["start_time"] == "2026-10-26T00:00:00Z"
    assert json.loads(json.dumps(records)) == records
    assert json.loads(result.model_dump(mode="json", indent=2))["records"] == records
