from __future__ import annotations

from typing import Any

from nbu.models.base import NbuModel


class Client(NbuModel):
    name: str
    os: str | None = None
    hardware: str | None = None
    policies: list[str] = []
    active: bool | None = None
    last_backup_status: str | int | None = None


def client_from_mapping(payload: dict[str, Any], source: str = "api") -> Client:
    attrs = payload.get("attributes", payload)
    return Client(
        name=attrs.get("clientName") or attrs.get("client_name") or attrs.get("name"),
        os=attrs.get("os") or attrs.get("operatingSystem") or attrs.get("operating_system"),
        hardware=attrs.get("hardware"),
        policies=attrs.get("policies", []) or [],
        active=attrs.get("active"),
        last_backup_status=attrs.get("lastBackupStatus") or attrs.get("last_backup_status"),
        raw=payload,
        source=source,
    )
