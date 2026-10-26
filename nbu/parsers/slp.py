from __future__ import annotations

from copy import deepcopy
from typing import Any

from nbu.models.slp import SLP, SLPOperation
from nbu.parsers.common import attributes, first_value, list_value, resource_id


def parse_slp_operation(payload: dict[str, Any], source: str = "api") -> SLPOperation:
    payload = deepcopy(payload)
    operation = first_value(payload, "operationType", "operation", "type")
    storage = payload.get("storage")
    target_storage = storage.get("name") if isinstance(storage, dict) else None
    if target_storage is None:
        target_storage = first_value(payload, "targetStorage", "target_storage")
    return SLPOperation(
        operation=str(operation or ""),
        target_storage=target_storage,
        retention=first_value(payload, "retentionPeriod", "retention"),
        retention_type=first_value(payload, "retentionType", "retention_type"),
        duplication=str(operation or "").upper() == "DUPLICATION",
        operation_index=first_value(payload, "operationIndex", "operation_index"),
        source_operation_index=first_value(
            payload, "sourceOperationIndex", "source_operation_index"
        ),
        storage=storage,
        flag_values=payload.get("flagValues") or [],
        alternate_read_server=payload.get("alternateReadServer"),
        target_import_slp=payload.get("targetImportSLP"),
        target_master_server=payload.get("targetMasterServer"),
        volume_pool=payload.get("volumePool"),
        preserve_multiplexing=payload.get("preserveMultiplexing"),
        operation_priority=payload.get("operationPriority"),
        slp_window_name=payload.get("slpWindowName"),
        raw=payload,
        source=source,
    )


def parse_slp(payload: dict[str, Any], source: str = "api") -> SLP:
    attrs = deepcopy(attributes(payload))
    operation_items = first_value(attrs, "operationList", "operations", "operation_list")
    operations = [
        parse_slp_operation(op, source)
        for op in list_value(operation_items)
        if isinstance(op, dict)
    ]
    return SLP(
        name=first_value(attrs, "slpName", "storage_lifecycle_policy", "slp", "name")
        or resource_id(payload)
        or "",
        active=attrs.get("active"),
        status=attrs.get("status"),
        operations=operations,
        # No invented lifecycle-wide values from an arbitrarily selected operation.
        retention=first_value(attrs, "retentionPeriod", "retention"),
        target_storage=first_value(attrs, "targetStorage", "target_storage"),
        version_number=attrs.get("versionNumber"),
        flag_values=attrs.get("flagValues") or [],
        data_classification=attrs.get("dataClassification"),
        duplication_priority=attrs.get("duplicationPriority"),
        raw=payload,
        source=source,
    )
