from __future__ import annotations

from copy import deepcopy
from typing import Any

from nbu.models.clients import Client
from nbu.models.policies import Policy, Schedule
from nbu.parsers.common import attributes, first_value, list_value, resource_id


def _policy_body(attrs: dict[str, Any]) -> dict[str, Any]:
    policy = attrs.get("policy")
    if isinstance(policy, dict):
        return policy
    # A flat body must not be mistaken for its policyAttributes child.
    if any(key in attrs for key in ("policyName", "policyType", "schedules", "clients")):
        return attrs
    candidates = [
        value
        for key, value in attrs.items()
        if key.startswith("policy")
        and key not in {"policyAttributes", "policy_attributes"}
        and isinstance(value, dict)
    ]
    return candidates[0] if len(candidates) == 1 else attrs


def _client_name(value: Any) -> str | None:
    if isinstance(value, dict):
        value = first_value(value, "hostName")
    return str(value) if isinstance(value, str | int) and value != "" else None


def _backup_selections(value: Any) -> list[str]:
    selections: list[str] = []
    for item in list_value(value):
        if isinstance(item, dict):
            nested = first_value(
                item, "selections", "selection", "backupSelections", "backup_selection"
            )
            selections.extend(_backup_selections(nested))
        elif isinstance(item, list):
            selections.extend(_backup_selections(item))
        elif isinstance(item, str) and item:
            selections.append(item)
    return selections


def _common_copy_value(copies: list[Any], *keys: str) -> Any:
    """Summarize only when every copy specifies the same value."""
    if not copies or not all(isinstance(copy, dict) for copy in copies):
        return None
    values = [first_value(copy, *keys) for copy in copies]
    return values[0] if all(value == values[0] for value in values) else None


def parse_schedule(payload: dict[str, Any], source: str = "api") -> Schedule:
    payload = deepcopy(payload)
    backup_copies = first_value(payload, "backupCopies", "backup_copies")
    copies = backup_copies.get("copies", []) if isinstance(backup_copies, dict) else []
    copies = copies if isinstance(copies, list) else []
    storage = first_value(payload, "storage", "storageUnit")
    if storage is None:
        storage = _common_copy_value(copies, "storage", "storageUnit")
    retention = first_value(payload, "retentionPeriod", "retention")
    if retention is None:
        retention = _common_copy_value(copies, "retentionPeriod", "retentionLevel")
    storage_is_slp = first_value(payload, "storageIsSLP", "storage_is_slp")
    return Schedule(
        schedule_name=first_value(payload, "scheduleName", "name") or "",
        schedule_type=first_value(payload, "scheduleType", "type"),
        backup_type=first_value(payload, "backupType", "backup_type"),
        storage_is_slp=storage_is_slp,
        slp=storage if storage and storage_is_slp is True else None,
        backup_copies=backup_copies,
        retention=retention,
        exclude_dates=first_value(payload, "excludeDates", "exclude_dates"),
        frequency_seconds=first_value(
            payload, "frequencySeconds", "frequency_seconds", "frequency"
        ),
        include_dates=first_value(payload, "includeDates", "include_dates"),
        start_window=first_value(payload, "startWindow", "start_window") or [],
        storage=storage,
        accelerator_forced_rescan=payload.get("acceleratorForcedRescan"),
        media_multiplexing=payload.get("mediaMultiplexing"),
        retries_allowed_after_run_day=payload.get("retriesAllowedAfterRunDay"),
        snapshot_only=payload.get("snapshotOnly"),
        synthetic_backup=payload.get("syntheticBackup"),
        raw=payload,
        source=source,
    )


def parse_policy_summary(payload: dict[str, Any], source: str = "api") -> Policy:
    attrs = deepcopy(attributes(payload))
    data = payload.get("data")
    resource = data if isinstance(data, dict) else payload
    policy_attrs = first_value(attrs, "policyAttributes", "policy_attributes")
    policy_attrs = policy_attrs if isinstance(policy_attrs, dict) else {}
    storage = first_value(policy_attrs, "storage", "storageUnit")
    if storage is None:
        storage = first_value(attrs, "storage", "storageUnit")
    storage_is_slp = first_value(policy_attrs, "storageIsSLP", "storage_is_slp")
    if storage_is_slp is None:
        storage_is_slp = first_value(attrs, "storageIsSLP", "storage_is_slp")
    item_type = resource.get("type")
    return Policy(
        name=str(
            first_value(attrs, "policyName", "policy_name", "name") or resource_id(payload) or ""
        ),
        policy_type=first_value(attrs, "policyType", "policy_type")
        or (item_type if item_type and item_type != "policy" else None),
        active=policy_attrs.get("active") if "active" in policy_attrs else attrs.get("active"),
        storage=storage,
        storage_is_slp=storage_is_slp,
        slp=storage if storage and storage_is_slp is True else None,
        configuration=attrs,
        policy_attributes=policy_attrs,
        raw=payload,
        source=source,
    )


def parse_policy_detail(payload: dict[str, Any], source: str = "api") -> Policy:
    attrs = deepcopy(_policy_body(attributes(payload)))
    # Reuse the summary mapping without changing the original resource envelope.
    resource = {"id": resource_id(payload), "attributes": attrs}
    policy = parse_policy_summary(resource, source)
    policy.raw = deepcopy(payload)
    policy.schedules = [
        parse_schedule(schedule, source)
        for schedule in list_value(first_value(attrs, "schedules", "schedule"))
        if isinstance(schedule, dict)
    ]
    policy.client_details = deepcopy(list_value(attrs.get("clients")))
    policy.clients = [
        name for client in policy.client_details if (name := _client_name(client)) is not None
    ]
    policy.backup_selections = _backup_selections(
        first_value(attrs, "backupSelections", "backup_selections")
    )
    policy.retention = first_value(
        policy.policy_attributes, "retention", "retentionPeriod", "retentionLevel"
    )
    if policy.retention is None:
        policy.retention = attrs.get("retention")
    return policy


def parse_protected_clients(policies: list[Policy], source: str = "policy") -> list[Client]:
    by_name: dict[str, set[str]] = {}
    for policy in policies:
        for client_name in policy.clients:
            by_name.setdefault(client_name, set()).add(policy.name)
    return [
        Client(name=name, policies=sorted(policy_names), source=source, raw={})
        for name, policy_names in sorted(by_name.items())
    ]
