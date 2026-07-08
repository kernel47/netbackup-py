from __future__ import annotations

from typing import Any

from nbu.models.slp import SLP, SLPOperation
from nbu.parsers.common import attributes, first_value, list_value, resource_id


def _simple_retention(value: Any) -> Any:
    if isinstance(value, dict):
        amount = first_value(value, "value", "amount")
        unit = first_value(value, "unit")
        if amount is not None and unit:
            return f"{amount} {unit}"
    return value


def parse_slp_operation(payload: dict[str, Any], source: str = "api") -> SLPOperation:
    operation = first_value(payload, "operation", "type", "operationType")
    storage = first_value(payload, "storage")
    target_storage = (
        first_value(storage, "name") if isinstance(storage, dict) else None
    ) or first_value(payload, "targetStorage", "target_storage")
    return SLPOperation(
        operation=str(operation or ""),
        target_storage=target_storage,
        retention=_simple_retention(first_value(payload, "retention", "retentionPeriod")),
        retention_type=first_value(payload, "retentionType", "retention_type"),
        duplication=str(operation or "").upper() == "DUPLICATION",
        operation_index=first_value(payload, "operationIndex", "operation_index"),
        source_operation_index=first_value(payload, "sourceOperationIndex", "source_operation_index"),
        storage=storage if isinstance(storage, dict) else None,
        raw=payload,
        source=source,
    )


def parse_slp(payload: dict[str, Any], source: str = "api") -> SLP:
    attrs = attributes(payload)
    operation_items = first_value(attrs, "operationList", "operations", "operation_list")
    operations = [
        parse_slp_operation(operation, source=source)
        for operation in list_value(operation_items)
        if isinstance(operation, dict)
    ]
    backup_operation = next(
        (operation for operation in operations if operation.operation.upper() == "BACKUP"),
        operations[0] if operations else None,
    )
    return SLP(
        name=first_value(attrs, "slpName", "storage_lifecycle_policy", "slp", "name")
        or resource_id(payload)
        or "",
        active=attrs.get("active"),
        status=attrs.get("status"),
        operations=operations,
        retention=_simple_retention(first_value(attrs, "retention", "retentionPeriod"))
        or (backup_operation.retention if backup_operation else None),
        target_storage=first_value(attrs, "targetStorage", "target_storage")
        or (backup_operation.target_storage if backup_operation else None),
        raw=payload,
        source=source,
    )
