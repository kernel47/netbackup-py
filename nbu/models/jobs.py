from __future__ import annotations

from datetime import datetime

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
    backup_id: str | None = None
