from __future__ import annotations

from typing import Any

from nbu.models.jobs import Job
from nbu.parsers.common import attributes, first_value, resource_id


def parse_job(payload: dict[str, Any], source: str = "api") -> Job:
    attrs = attributes(payload)
    return Job(
        id=first_value(attrs, "jobId", "jobid", "id", "job_id") or resource_id(payload) or "",
        parent_job_id=first_value(attrs, "parentJobId", "parent_job_id"),
        type=first_value(attrs, "jobType", "type"),
        state=attrs.get("state"),
        status=attrs.get("status"),
        status_description=first_value(attrs, "statusDescription", "status_description"),
        policy=first_value(attrs, "policyName", "policy_name", "policy"),
        client=first_value(attrs, "clientName", "client_name", "client"),
        schedule=first_value(attrs, "scheduleName", "schedule_name", "schedule"),
        storage_unit=first_value(attrs, "storageUnit", "storage_unit"),
        start_time=first_value(attrs, "startTime", "start_time"),
        end_time=first_value(attrs, "endTime", "end_time"),
        elapsed_seconds=first_value(attrs, "elapsedSeconds", "elapsed_seconds"),
        kilobytes=first_value(attrs, "kilobytesTransferred", "kilobytes", "kb"),
        files=first_value(attrs, "filesTransferred", "files"),
        percent_complete=first_value(attrs, "percentComplete", "percent_complete"),
        backup_id=first_value(attrs, "backupId", "backup_id"),
        source=source,
        raw=payload,
    )
