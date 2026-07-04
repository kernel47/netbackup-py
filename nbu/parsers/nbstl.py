from __future__ import annotations

from nbu.models.slp import SLP, slp_from_mapping
from nbu.parsers.common import split_key_value_lines


def parse(text: str) -> list[SLP]:
    slps: list[SLP] = []
    for record in split_key_value_lines(text):
        name = record.get("storage_lifecycle_policy") or record.get("slp") or record.get("name")
        if name:
            slps.append(slp_from_mapping(record | {"name": name}, source="ssh"))
    return slps

