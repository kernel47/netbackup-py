from __future__ import annotations

from nbu.models.storage import StorageUnit, storage_unit_from_mapping
from nbu.parsers.common import split_key_value_lines


def parse(text: str) -> list[StorageUnit]:
    units: list[StorageUnit] = []
    for record in split_key_value_lines(text):
        name = record.get("storage_unit") or record.get("name")
        if name:
            units.append(storage_unit_from_mapping(record | {"name": name}, source="ssh"))
    return units

