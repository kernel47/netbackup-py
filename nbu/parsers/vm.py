from __future__ import annotations

from typing import Any

from nbu.models.vm import VMwareClient, VMwareSelection, VMwareTestQuery
from nbu.parsers.common import attributes, first_value, resource_id


def parse_vmware_selection(raw: str) -> VMwareSelection | None:
    if "filter=" not in raw or not raw.startswith("vmware:"):
        return None
    query_filter = raw.split("filter=", 1)[1].strip()
    if not query_filter:
        return None
    return VMwareSelection(raw=raw, query_filter=query_filter)


def parse_vmware_client(payload: dict[str, Any], source: str = "api") -> VMwareClient:
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


def parse_test_query(payload: dict[str, Any], source: str = "api") -> VMwareTestQuery:
    attrs = attributes(payload)
    query_id = (
        first_value(attrs, "testQueryId", "test_query_id", "queryId")
        or resource_id(payload)
        or payload.get("testQueryId")
    )
    done = first_value(attrs, "isDiscoveryDone", "discoveryDone", "done")
    return VMwareTestQuery(
        test_query_id=str(query_id),
        done=bool(done) if done is not None else None,
        raw=payload,
        source=source,
    )


def parse_test_query_clients(payload: dict[str, Any], source: str = "api") -> list[VMwareClient]:
    return [
        parse_vmware_client(item, source=source)
        for item in _candidate_client_items(payload)
        if isinstance(item, dict)
    ]


def _candidate_client_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for entry in value for item in _candidate_client_items(entry)]
    if not isinstance(value, dict):
        return []

    attrs = attributes(value)
    name = first_value(attrs, "displayName", "vmName", "virtualMachineName", "name")
    if name is not None:
        return [value]

    items: list[dict[str, Any]] = []
    for key in (
        "data",
        "results",
        "items",
        "assets",
        "vms",
        "virtualMachines",
        "discoveredAssets",
        "discoveredVms",
        "discoveryResults",
        "queryResults",
    ):
        child = value.get(key)
        if child is not None:
            items.extend(_candidate_client_items(child))

    raw_attrs = value.get("attributes")
    if isinstance(raw_attrs, dict):
        items.extend(_candidate_client_items(raw_attrs))
    return items
