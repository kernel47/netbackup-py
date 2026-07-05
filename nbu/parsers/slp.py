from __future__ import annotations

from typing import Any

from nbu.models.slp import SLP, SLPOperation
from nbu.parsers.common import attributes, first_value, list_value, resource_id


def parse_slp_operation(payload: dict[str, Any], source: str = "api") -> SLPOperation:
    operation = first_value(payload, "operation", "type")
    return SLPOperation(
        operation=operation,
        target_storage=first_value(payload, "targetStorage", "target_storage", "storage"),
        retention=payload.get("retention"),
        duplication=operation == "duplication",
        raw=payload,
        source=source,
    )


def parse_slp(payload: dict[str, Any], source: str = "api") -> SLP:
    attrs = attributes(payload)
    operations = [
        parse_slp_operation(operation, source=source)
        for operation in list_value(attrs.get("operations"))
        if isinstance(operation, dict)
    ]
    return SLP(
        name=first_value(attrs, "slpName", "storage_lifecycle_policy", "slp", "name")
        or resource_id(payload),
        status=attrs.get("status"),
        operations=operations,
        retention=attrs.get("retention"),
        target_storage=first_value(attrs, "targetStorage", "target_storage"),
        raw=payload,
        source=source,
    )
