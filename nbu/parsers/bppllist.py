from __future__ import annotations

from nbu.models.policies import Policy, policy_from_mapping
from nbu.parsers.common import split_key_value_lines


def parse(text: str) -> list[Policy]:
    policies: list[Policy] = []
    for record in split_key_value_lines(text):
        name = record.get("policy_name") or record.get("name") or record.get("class")
        if not name:
            continue
        payload = {
            "name": name,
            "policy_type": record.get("policy_type") or record.get("type"),
            "active": record.get("active", "").lower() in {"yes", "true", "1", "active"},
            "clients": [c.strip() for c in record.get("clients", "").split(",") if c.strip()],
            "backup_selections": [
                s.strip() for s in record.get("backup_selections", "").split(",") if s.strip()
            ],
            "storage": record.get("storage") or record.get("storage_unit"),
        }
        policies.append(policy_from_mapping(payload, source="ssh"))
    return policies

