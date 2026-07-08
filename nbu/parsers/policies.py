from __future__ import annotations

from typing import Any

from nbu.models.clients import Client
from nbu.models.policies import Policy, Schedule
from nbu.parsers.common import attributes, first_value, list_value, resource_id


def _policy_body(attrs: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(attrs, dict):
        return {}
    for key, value in attrs.items():
        if key.startswith("policy") and isinstance(value, dict):
            return value
    policy = attrs.get("policy")
    if isinstance(policy, dict):
        return policy
    return attrs


def _client_name(value: Any) -> str | None:
    if isinstance(value, dict):
        name = first_value(value, "hostName")
        return str(name) if name is not None else None
    return str(value) if value not in {None, ""} else None


def _backup_selections(value: Any) -> list[str]:
    selections: list[str] = []
    for item in list_value(value):
        if item is None or item == "":
            continue
        if isinstance(item, dict):
            nested = first_value(item, "selections", "selection", "backupSelections", "backup_selection")
            selections.extend(_backup_selections(nested))
        elif isinstance(item, list):
            selections.extend(_backup_selections(item))
        else:
            selections.append(str(item))
    return selections


def _first_copy(payload: dict[str, Any]) -> dict[str, Any]:
    backup_copies = first_value(payload, "backupCopies", "backup_copies")
    if not isinstance(backup_copies, dict):
        return {}
    copies = backup_copies.get("copies")
    return copies[0] if isinstance(copies, list) and isinstance(copies[0], dict) else {}


def _retention(payload: dict[str, Any], copy: dict[str, Any]) -> Any:
    return first_value(
        copy,
        "retentionPeriod",
        "retentionLevel",
        "retention",
    ) or first_value(payload, "retention", "retentionPeriod", "retentionLevel")


def parse_schedule(payload: dict[str, Any], source: str = "api") -> Schedule:
    if not isinstance(payload, dict):
        payload = {}
    copy = _first_copy(payload)
    retention = _retention(payload, copy)
    storage = first_value(copy, "storage", "storageUnit") or first_value(
        payload, "storage", "storageUnit"
    )
    storage_is_slp = first_value(payload, "storageIsSLP", "storage_is_slp")
    return Schedule(
        name=first_value(payload, "name", "scheduleName") or "",
        type=first_value(payload, "type", "scheduleType"),
        backup_type=first_value(payload, "backupType", "backup_type"),
        retention=retention,
        retention_period=first_value(copy, "retentionPeriod") or first_value(payload, "retentionPeriod"),
        frequency_seconds=first_value(payload, "frequencySeconds", "frequency_seconds", "frequency"),
        include_dates=first_value(payload, "includeDates", "include_dates"),
        exclude_dates=first_value(payload, "excludeDates", "exclude_dates"),
        start_window=[
            item for item in list_value(first_value(payload, "startWindow", "start_window"))
            if isinstance(item, dict)
        ],
        storage=storage,
        storage_is_slp=storage_is_slp if isinstance(storage_is_slp, bool) else None,
        slp_name=str(storage) if storage and storage_is_slp is True else None,
        raw=payload,
        source=source,
    )


def parse_policy_summary(payload: dict[str, Any], source: str = "api") -> Policy:
    attrs = attributes(payload)
    item_type = payload.get("type")
    policy_attrs = first_value(attrs, "policyAttributes", "policy_attributes") or {}
    policy_attrs = policy_attrs if isinstance(policy_attrs, dict) else {}
    storage = first_value(policy_attrs, "storage", "storageUnit") or first_value(
        attrs, "storage", "storageUnit"
    )
    storage_is_slp = first_value(policy_attrs, "storageIsSLP", "storage_is_slp")
    return Policy(
        name=str(first_value(attrs, "policyName", "policy_name", "name") or resource_id(payload) or ""),
        policy_type=first_value(attrs, "policyType", "policy_type")
        or (item_type if item_type and item_type != "policy" else None),
        active=first_value(policy_attrs, "active") if "active" in policy_attrs else attrs.get("active"),
        storage=storage,
        storage_is_slp=storage_is_slp if isinstance(storage_is_slp, bool) else None,
        slp_name=str(storage) if storage and storage_is_slp is True else None,
        raw=payload,
        source=source,
    )


def parse_policy_detail(payload: dict[str, Any], source: str = "api") -> Policy:
    attrs = _policy_body(attributes(payload))
    policy_attrs = first_value(attrs, "policyAttributes", "policy_attributes") or {}
    policy_attrs = policy_attrs if isinstance(policy_attrs, dict) else {}
    schedules = [
        parse_schedule(schedule, source=source)
        for schedule in list_value(first_value(attrs, "schedules", "schedule"))
        if isinstance(schedule, dict)
    ]
    clients = [
        name
        for name in (_client_name(client) for client in list_value(attrs.get("clients")))
        if name is not None
    ]
    storage = first_value(policy_attrs, "storage", "storageUnit") or first_value(
        attrs, "storage", "storageUnit"
    )
    storage_is_slp = first_value(policy_attrs, "storageIsSLP", "storage_is_slp")
    return Policy(
        name=str(first_value(attrs, "policyName", "policy_name", "name") or resource_id(payload) or ""),
        policy_type=first_value(attrs, "policyType", "policy_type"),
        active=first_value(policy_attrs, "active") if "active" in policy_attrs else attrs.get("active"),
        clients=clients,
        schedules=schedules,
        backup_selections=_backup_selections(first_value(attrs, "backupSelections", "backup_selections")),
        retention=first_value(policy_attrs, "retention", "retentionPeriod", "retentionLevel")
        or attrs.get("retention"),
        storage=storage,
        storage_is_slp=storage_is_slp if isinstance(storage_is_slp, bool) else None,
        slp_name=str(storage) if storage and storage_is_slp is True else None,
        raw=payload,
        source=source,
    )


def parse_protected_clients(policies: list[Policy], source: str = "policy") -> list[Client]:
    by_name: dict[str, set[str]] = {}
    for policy in policies:
        for client_name in policy.clients:
            by_name.setdefault(client_name, set()).add(policy.name)

    return [
        Client(name=name or "", policies=sorted(policy_names), source=source, raw={})
        for name, policy_names in sorted(by_name.items())
    ]
