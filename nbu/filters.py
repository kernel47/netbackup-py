"""Small helpers for NetBackup OData-style filter strings."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any


def quote_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, datetime):
        value = value.isoformat()
    elif isinstance(value, date):
        value = value.isoformat()
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def expr(field: str, operator: str, value: Any) -> str:
    return f"{field} {operator} {quote_value(value)}"


def contains(field: str, value: Any) -> str:
    escaped = str(value).replace("'", "''")
    return f"contains({field},'{escaped}')"


def combine(*parts: str | None) -> str | None:
    clean = [part for part in parts if part]
    return " and ".join(clean) if clean else None

