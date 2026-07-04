from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from nbu.models.base import NbuModel


class Job(NbuModel):
    job_id: int | str = Field(alias="id")
    parent_job_id: int | str | None = None
    type: str | None = None
    state: str | None = None
    status: int | str | None = None
    status_description: str | None = None
    policy: str | None = None
    client: str | None = None
    schedule: str | None = None
    storage_unit: str | None = None
    start_time: datetime | str | None = None
    end_time: datetime | str | None = None
    elapsed_seconds: int | None = None
    kilobytes: int | None = None
    files: int | None = None
    percent_complete: int | None = None


def job_from_mapping(payload: dict[str, Any], source: str = "api") -> Job:
    attrs = payload.get("attributes", payload)
    return Job(
        id=attrs.get("jobId") or attrs.get("jobid") or attrs.get("id") or attrs.get("job_id"),
        parent_job_id=attrs.get("parentJobId") or attrs.get("parent_job_id"),
        type=attrs.get("jobType") or attrs.get("type"),
        state=attrs.get("state"),
        status=attrs.get("status"),
        status_description=attrs.get("statusDescription") or attrs.get("status_description"),
        policy=attrs.get("policyName") or attrs.get("policy_name") or attrs.get("policy"),
        client=attrs.get("clientName") or attrs.get("client_name") or attrs.get("client"),
        schedule=attrs.get("scheduleName") or attrs.get("schedule_name") or attrs.get("schedule"),
        storage_unit=attrs.get("storageUnit") or attrs.get("storage_unit"),
        start_time=attrs.get("startTime") or attrs.get("start_time"),
        end_time=attrs.get("endTime") or attrs.get("end_time"),
        elapsed_seconds=attrs.get("elapsedSeconds") or attrs.get("elapsed_seconds"),
        kilobytes=attrs.get("kilobytes") or attrs.get("kb"),
        files=attrs.get("files"),
        percent_complete=attrs.get("percentComplete") or attrs.get("percent_complete"),
        source=source,
        raw=payload,
    )
