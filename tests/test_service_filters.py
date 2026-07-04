import httpx

from nbu.config import NetBackupConfig
from nbu.services.images import ImagesService
from nbu.services.jobs import JobsService
from nbu.transport.api import ApiTransport
from nbu.version import VersionManager


def test_jobs_filter_uses_cursor_pagination_and_raw_iso_dates() -> None:
    seen: dict[str, str | None] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["filter"] = request.url.params.get("filter")
        seen["after"] = request.url.params.get("page[after]")
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "100",
                        "attributes": {
                            "jobId": 100,
                            "jobType": "BACKUP",
                            "startTime": "2026-07-01T00:10:00Z",
                            "status": 0,
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
    service = JobsService(api.config, api, VersionManager("10.0"))

    jobs = service.list(
        start_date="2026-07-01T00:00:00Z",
        end_date="2026-07-02T00:00:00Z",
        filter="status eq 0",
        type="BACKUP",
    )

    assert jobs[0].job_id == 100
    assert seen["after"] is None
    assert seen["filter"] == (
        "status eq 0 and startTime ge 2026-07-01T00:00:00Z and "
        "startTime le 2026-07-02T00:00:00Z and jobType eq 'BACKUP'"
    )


def test_images_filter_uses_offset_pagination_and_custom_filter() -> None:
    seen: dict[str, str | None] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["filter"] = request.url.params.get("filter")
        seen["offset"] = request.url.params.get("page[offset]")
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "app01_123",
                        "attributes": {
                            "backupId": "app01_123",
                            "clientName": "app01",
                            "policyType": "STANDARD",
                            "scheduleType": "FULL",
                            "backupTime": "2026-07-01T00:10:00Z",
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
    service = ImagesService(api.config, api, VersionManager("10.0"))

    images = service.list(
        client="app01",
        start_date="2026-07-01T00:00:00Z",
        filter="scheduleType eq 'FULL'",
    )

    assert images[0].backup_id == "app01_123"
    assert images[0].schedule_type == "FULL"
    assert seen["offset"] is None
    assert seen["filter"] == (
        "scheduleType eq 'FULL' and clientName eq 'app01' and "
        "backupTime ge 2026-07-01T00:00:00Z"
    )
