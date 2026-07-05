from __future__ import annotations

from datetime import datetime

from nbu.models.base import NbuModel


class Image(NbuModel):
    image_id: str
    backup_id: str | None = None
    client: str | None = None
    policy: str | None = None
    policy_type: str | None = None
    schedule: str | None = None
    schedule_type: str | None = None
    backup_time: datetime | str | None = None
    expiration_time: datetime | str | None = None
    retention_level: str | int | None = None
    copy_number: int | None = None
    storage_location: str | None = None
    kilobytes: int | None = None
