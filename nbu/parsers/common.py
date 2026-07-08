from __future__ import annotations

from typing import Any


def attributes(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    data = payload.get("data")
    if isinstance(data, dict):
        payload = data
    attrs = payload.get("attributes")
    return attrs if isinstance(attrs, dict) else payload


def resource_id(payload: dict[str, Any]) -> Any:
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    if isinstance(data, dict):
        return data.get("id")
    return payload.get("id")


def first_value(mapping: dict[str, Any], *keys: str) -> Any:
    if not isinstance(mapping, dict):
        return None
    for key in keys:
        value = mapping.get(key)
        if value is not None and value != "":
            return value
    return None


def list_value(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
