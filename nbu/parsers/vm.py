from __future__ import annotations

from typing import Any

from nbu.models.vm import VMwareClient, VMwareSelection
from nbu.parsers.common import attributes, first_value, resource_id


def parse_vmware_selection(raw: str) -> VMwareSelection | None:
    if "filter=" not in raw or not raw.startswith("vmware:"):
        return None
    query_filter = raw.split("filter=", 1)[1].strip()
    if not query_filter:
        return None
    return VMwareSelection(raw=raw, query_filter=query_filter)


def parse_preview_client(payload: dict[str, Any], source: str = "api") -> VMwareClient:
    attrs = attributes(payload)
    name = first_value(
        attrs,
        "displayName",
        "vmName",
        "virtualMachineName",
        "name",
        "hostName",
        "clientName",
    ) or resource_id(payload)
    return VMwareClient(
        name=str(name),
        id=str(resource_id(payload)) if resource_id(payload) is not None else None,
        raw=payload,
        source=source,
    )
