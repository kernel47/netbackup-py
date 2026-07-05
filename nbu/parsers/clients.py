from __future__ import annotations

from typing import Any

from nbu.models.clients import Client
from nbu.parsers.common import attributes, first_value, list_value, resource_id


def parse_host(payload: dict[str, Any], source: str = "api") -> Client:
    attrs = attributes(payload)
    return Client(
        name=first_value(attrs, "hostName", "clientName", "client_name", "name") or resource_id(payload),
        os=first_value(attrs, "os", "operatingSystem", "operating_system"),
        hardware=attrs.get("hardware"),
        policies=[str(policy) for policy in list_value(attrs.get("policies"))],
        active=attrs.get("active"),
        last_backup_status=first_value(attrs, "lastBackupStatus", "last_backup_status"),
        raw=payload,
        source=source,
    )
