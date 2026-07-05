from __future__ import annotations

from typing import Any

from nbu.models.clients import Client
from nbu.models.policies import Policy, Schedule
from nbu.parsers.common import attributes, first_value, list_value, resource_id


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
    return Policy(
        name=first_value(attrs, "policyName", "policy_name", "name") or resource_id(payload),
        policy_type=first_value(attrs, "policyType", "policy_type"),
        active=attrs.get("active"),
        storage=first_value(attrs, "storage", "storageUnit"),
        raw=payload,
        source=source,
    )


def parse_policy_detail(payload: dict[str, Any], source: str = "api") -> Policy:
    attrs = attributes(payload)
    schedules = [
        parse_schedule(schedule, source=source)
        for schedule in list_value(first_value(attrs, "schedules", "schedule"))
        if isinstance(schedule, dict)
    ]
    return Policy(
        name=first_value(attrs, "policyName", "policy_name", "name") or resource_id(payload),
        policy_type=first_value(attrs, "policyType", "policy_type"),
        active=attrs.get("active"),
        clients=[str(client) for client in list_value(attrs.get("clients"))],
        schedules=schedules,
        backup_selections=[
            str(selection)
            for selection in list_value(first_value(attrs, "backupSelections", "backup_selections"))
        ],
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
