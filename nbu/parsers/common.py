"""Parser utility helpers."""

from __future__ import annotations


def split_key_value_lines(text: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                records.append(current)
                current = {}
            continue
        if ":" in line:
            key, value = line.split(":", 1)
        elif "=" in line:
            key, value = line.split("=", 1)
        else:
            continue
        current[key.strip().lower().replace(" ", "_")] = value.strip()
    if current:
        records.append(current)
    return records


def split_csvish(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        rows.append([part.strip() for part in line.split(",")])
    return rows

