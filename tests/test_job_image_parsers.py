"""Regression payloads using official admin/catalog fields from API 7.0, 9.0, 12.0, 14.0.

Source URLs and format changes are recorded in documentation.md.
"""

from copy import deepcopy

import httpx
import pytest

from nbu.config import NetBackupConfig
from nbu.parsers.images import parse_image
from nbu.parsers.jobs import parse_job
from nbu.services.images import ImagesService
from nbu.services.jobs import JobsService
from nbu.transport.api import ApiTransport
from nbu.version import VersionManager


@pytest.mark.parametrize("duration", ["25:10:05", "PT25H10M5S", "PT0S", "P2DT3H4M5S"])
@pytest.mark.parametrize("wrapped", [False, True])
def test_jobs_official_fields_preserve_duration_and_counts(duration, wrapped):
    resource = {
        "id": "not-the-job-id",
        "type": "job",
        "attributes": {
            "jobId": 0,
            "parentJobId": 0,
            "numberOfFiles": 0,
            "kilobytesTransferred": 100,
            "kilobytesDataTransferred": 12,
            "kilobytesToTransfer": 200,
            "elapsedTime": duration,
            "activeElapsedTime": "PT0S",
            "percentComplete": 0,
            "status": 0,
            "sourceStorageUnitName": "disk-source",
            "destinationStorageUnitName": "tape-destination",
            "lastUpdateTime": "2026-10-26T00:00:00Z",
            "futureField": {"flags": [False, 0]},
        },
    }
    payload = {"data": resource} if wrapped else resource
    original = deepcopy(payload)
    job = parse_job(payload)
    assert job.job_id == 0
    assert job.parent_job_id == 0
    assert job.files == 0
    assert job.percent_complete == 0
    assert job.status == 0
    assert job.elapsed_time == duration
    assert job.active_elapsed_time == "PT0S"
    assert job.elapsed_seconds is None  # no guessed conversion of legacy/ISO durations
    assert job.kilobytes == 100
    assert job.kilobytes_data_transferred == 12
    assert job.kilobytes_to_transfer == 200
    assert job.source_storage_unit == "disk-source"
    assert job.destination_storage_unit == "tape-destination"
    assert job.storage_unit is None  # source and destination are distinct fields
    assert job.last_update_time == "2026-10-26T00:00:00Z"
    assert payload == original
    assert job.raw == original
    payload.clear()
    assert job.raw == original


def test_job_explicit_null_or_empty_is_not_replaced_by_an_alias():
    job = parse_job(
        {
            "attributes": {
                "numberOfFiles": None,
                "filesTransferred": 99,
                "policyName": "",
                "policy": "other",
                "kilobytesTransferred": 0,
                "kilobytes": 99,
            }
        }
    )
    assert job.files is None
    assert job.policy == ""
    assert job.kilobytes == 0


@pytest.mark.parametrize("expiration", [None, "2026-12-31T23:59:59Z"])
@pytest.mark.parametrize("wrapped", [False, True])
def test_images_official_fields_keep_every_fragment(expiration, wrapped):
    resource = {
        "id": "app01_123",
        "type": "image",
        "attributes": {
            "clientName": "app01",
            "policyName": "prod",
            "policyType": "Standard",
            "kbytes": 0,
            "expiration": expiration,
            "retentionLevel": 0,
            "numCopies": 2,
            "primaryCopy": 2,
            "numFiles": 0,
            "elapsedTimeSeconds": 0,
            "slpName": "gold",
            "slpVersion": 3,
            "fragments": [
                {
                    "copyNumber": 1,
                    "fragmentNumber": 1,
                    "mediaId": "/disk/a",
                    "expiration": None,
                    "kbytes64": 0,
                    "custom": {"disabled": False},
                },
                {
                    "copyNumber": 2,
                    "fragmentNumber": 1,
                    "mediaId": "TAPE01",
                    "expiration": "2027-01-01T00:00:00Z",
                    "retentionLevel": 9,
                },
            ],
            "futureField": {"flags": [False, 0]},
        },
    }
    payload = {"data": resource} if wrapped else resource
    original = deepcopy(payload)
    image = parse_image(payload)
    assert image.image_id == image.backup_id == "app01_123"
    assert image.kilobytes == 0
    assert image.expiration_time == expiration
    assert image.retention_level == 0
    assert image.num_copies == 2
    assert image.primary_copy == 2
    assert image.copy_number is None  # primaryCopy does not describe all fragments
    assert image.storage_location is None  # no arbitrary fragment selected
    assert image.num_files == image.elapsed_seconds == 0
    assert (image.slp_name, image.slp_version) == ("gold", 3)
    assert image.fragments == resource["attributes"]["fragments"]
    assert image.raw == original
    image.fragments[0]["custom"]["disabled"] = True
    assert payload == original
    assert image.raw == original
    payload.clear()
    assert image.raw == original


def test_image_explicit_infinite_expiration_does_not_fall_back_to_legacy_alias():
    image = parse_image(
        {
            "attributes": {
                "expiration": None,
                "expirationTime": "stale",
                "kbytes": 0,
                "kilobytes": 99,
                "storage": {"destinations": ["disk", "tape"]},
            }
        }
    )
    assert image.expiration_time is None
    assert image.kilobytes == 0
    assert image.storage_location is None
    assert image.raw["attributes"]["storage"] == {"destinations": ["disk", "tape"]}


def test_legacy_aliases_still_work():
    job = parse_job(
        {
            "id": "123",
            "attributes": {
                "filesTransferred": 4,
                "elapsedSeconds": 12,
                "storageUnit": "disk",
                "kilobytes": 8,
            },
        }
    )
    assert (job.files, job.elapsed_seconds, job.storage_unit, job.kilobytes) == (4, 12, "disk", 8)
    image = parse_image(
        {
            "id": "host_123",
            "attributes": {"expirationTime": "date", "kilobytes": 5, "copyNumber": 3},
        }
    )
    assert (image.expiration_time, image.kilobytes, image.copy_number) == ("date", 5, 3)


@pytest.mark.parametrize(
    "release,duration",
    [
        ("10.0", "00:00:01"),
        ("10.1.1", "PT1S"),
        ("10.5", "PT1S"),
        ("11.1", "PT1S"),
        ("11.2", "PT1S"),
    ],
)
def test_services_parse_list_and_detail_without_rewriting_api(release, duration):
    job_resource = {
        "id": "1",
        "attributes": {"jobId": 1, "numberOfFiles": 3, "elapsedTime": duration},
    }
    image_resource = {
        "id": "host_1",
        "attributes": {"kbytes": 42, "expiration": None, "fragments": [{"copyNumber": 1}]},
    }

    def handler(request):
        resource = job_resource if "/admin/jobs" in request.url.path else image_resource
        is_detail = request.url.path.endswith(("/1", "/host_1"))
        return httpx.Response(
            200,
            json={
                "data": resource if is_detail else [resource],
                "meta": {"pagination": {"hasNext": False}},
            },
        )

    config = NetBackupConfig(master="m", token="t", version=release)
    with_api = ApiTransport(config, transport=httpx.MockTransport(handler))
    try:
        jobs = JobsService(config, with_api, VersionManager(release))
        images = ImagesService(config, with_api, VersionManager(release))
        assert jobs.list()[0].files == jobs.get(1).files == 3
        assert jobs.get(1).elapsed_time == duration
        assert images.list()[0].kilobytes == images.get("host_1").kilobytes == 42
        assert images.get("host_1").raw["data"] == image_resource
        assert jobs.get(1).raw["data"] == job_resource
    finally:
        with_api.close()
