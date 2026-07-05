from __future__ import annotations

from typing import Any

from nbu.models.clients import Client
from nbu.models.policies import Policy, Schedule
from nbu.parsers.common import attributes, first_value, list_value, resource_id


def _policy_body(attrs: dict[str, Any]) -> dict[str, Any]:
    for key, value in attrs.items():
        if key.startswith("policy") and isinstance(value, dict):
            return value
    policy = attrs.get("policy")
    if isinstance(policy, dict):
        return policy
    return attrs


def _client_name(value: Any) -> str | None:
    if isinstance(value, dict):
        name = first_value(value, "hostName", "clientName", "name")
        return str(name) if name is not None else None
    return str(value) if value not in {None, ""} else None


def _strings(value: Any) -> list[str]:
    return [str(item) for item in list_value(value) if item not in {None, ""}]


def _vmware_odata_filters(attrs: dict[str, Any]) -> list[str]:
    filters: list[str] = []
    for value in list_value(
        first_value(attrs, "vmwareIntelligentClientSelections", "vmware_intelligent_client_selections")
    ):
        if isinstance(value, str) and value:
            filters.append(value)
        elif isinstance(value, dict):
            filter_value = first_value(value, "filter", "odataFilter", "oDataFilter", "query")
            if filter_value:
                filters.append(str(filter_value))
    return filters


def parse_schedule(payload: dict[str, Any], source: str = "api") -> Schedule:
    return Schedule(
        name=first_value(payload, "name", "scheduleName"),
        type=first_value(payload, "type", "scheduleType"),
        retention=first_value(payload, "retention", "retentionLevel"),
        frequency_seconds=first_value(payload, "frequencySeconds", "frequency_seconds"),
        calendar=payload.get("calendar"),
        raw=payload,
        source=source,
    )


def parse_policy_summary(payload: dict[str, Any], source: str = "api") -> Policy:
    attrs = attributes(payload)
    item_type = payload.get("type")
    return Policy(
        name=first_value(attrs, "policyName", "policy_name", "name") or resource_id(payload),
        policy_type=first_value(attrs, "policyType", "policy_type")
        or (item_type if item_type and item_type != "policy" else None),
        active=attrs.get("active"),
        storage=first_value(attrs, "storage", "storageUnit"),
        raw=payload,
        source=source,
    )


def parse_policy_detail(payload: dict[str, Any], source: str = "api") -> Policy:
    attrs = _policy_body(attributes(payload))
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
    return Policy(
        name=first_value(attrs, "policyName", "policy_name", "name") or resource_id(payload),
        policy_type=first_value(attrs, "policyType", "policy_type"),
        active=attrs.get("active"),
        clients=clients,
        schedules=schedules,
        backup_selections=_strings(first_value(attrs, "backupSelections", "backup_selections")),
        vmware_odata_filters=_vmware_odata_filters(attrs),
        retention=attrs.get("retention"),
        storage=first_value(attrs, "storage", "storageUnit"),
        raw=payload,
        source=source,
    )


def parse_protected_clients(policies: list[Policy], source: str = "policy") -> list[Client]:
    by_name: dict[str, set[str]] = {}
    for policy in policies:
        for client_name in policy.clients:
            by_name.setdefault(client_name, set()).add(policy.name)

    return [
        Client(name=name, policies=sorted(policy_names), source=source, raw={})
        for name, policy_names in sorted(by_name.items())
    ]


def parse_unique_policy_client(payload: dict[str, Any], source: str = "api") -> Client:
    attrs = attributes(payload)
    return Client(
        name=resource_id(payload) or first_value(attrs, "clientName", "hostName", "name"),
        os=first_value(attrs, "OS", "os", "operatingSystem"),
        hardware=attrs.get("hardware"),
        policies=[str(policy) for policy in list_value(first_value(attrs, "policyNames", "policies"))],
        raw=payload,
        source=source,
    )
