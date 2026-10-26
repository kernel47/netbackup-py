from __future__ import annotations

from copy import deepcopy
from typing import Any

from nbu.models.jobs import Job
from nbu.parsers.common import attributes, first_present, resource_id


def parse_job(payload: dict[str, Any], source: str = "api") -> Job:
    attrs = deepcopy(attributes(payload))
    job_id = first_present(attrs, "jobId", "jobid", "id", "job_id")
    if job_id is None:
        job_id = resource_id(payload)
    return Job(
        id=job_id if job_id is not None else "",
        parent_job_id=first_present(attrs, "parentJobId", "parent_job_id"),
        type=first_present(attrs, "jobType", "type"),
        state=attrs.get("state"),
        status=attrs.get("status"),
        status_description=first_present(attrs, "statusDescription", "status_description"),
        policy=first_present(attrs, "policyName", "policy_name", "policy"),
        client=first_present(attrs, "clientName", "client_name", "client"),
        schedule=first_present(attrs, "scheduleName", "schedule_name", "schedule"),
        storage_unit=first_present(attrs, "storageUnit", "storage_unit"),
        start_time=first_present(attrs, "startTime", "start_time"),
        end_time=first_present(attrs, "endTime", "end_time"),
        elapsed_seconds=first_present(attrs, "elapsedSeconds", "elapsed_seconds"),
        kilobytes=first_present(attrs, "kilobytesTransferred", "kilobytes", "kb"),
        files=first_present(attrs, "numberOfFiles", "filesTransferred", "files"),
        percent_complete=first_present(attrs, "percentComplete", "percent_complete"),
        backup_id=first_present(attrs, "backupId", "backup_id"),
        elapsed_time=attrs.get("elapsedTime"),
        active_elapsed_time=attrs.get("activeElapsedTime"),
        last_update_time=attrs.get("lastUpdateTime"),
        source_storage_unit=attrs.get("sourceStorageUnitName"),
        destination_storage_unit=attrs.get("destinationStorageUnitName"),
        kilobytes_data_transferred=attrs.get("kilobytesDataTransferred"),
        kilobytes_to_transfer=attrs.get("kilobytesToTransfer"),
        source=source,
        raw=payload,
    )
