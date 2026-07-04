from __future__ import annotations

from typing import Any

from nbu.models.base import NbuModel


class SLPOperation(NbuModel):
    operation: str
    target_storage: str | None = None
    retention: str | int | None = None
    duplication: bool | None = None


class SLP(NbuModel):
    name: str
    status: str | None = None
    operations: list[SLPOperation] = []
    retention: str | int | None = None
    target_storage: str | None = None


def slp_from_mapping(payload: dict[str, Any], source: str = "api") -> SLP:
    attrs = payload.get("attributes", payload)
    operations = [
        SLPOperation(
            operation=o.get("operation") or o.get("type"),
            target_storage=o.get("targetStorage") or o.get("target_storage") or o.get("storage"),
            retention=o.get("retention"),
            duplication=(o.get("operation") or o.get("type")) == "duplication",
            raw=o,
            source=source,
        )
        for o in attrs.get("operations", []) or []
    ]
    return SLP(
        name=attrs.get("slpName") or attrs.get("storage_lifecycle_policy") or attrs.get("slp") or attrs.get("name"),
        status=attrs.get("status"),
        operations=operations,
        retention=attrs.get("retention"),
        target_storage=attrs.get("targetStorage") or attrs.get("target_storage"),
        raw=payload,
        source=source,
    )
