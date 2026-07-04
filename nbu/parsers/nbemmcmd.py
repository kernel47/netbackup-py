from __future__ import annotations

from nbu.models.clients import Client, client_from_mapping
from nbu.parsers.common import split_key_value_lines


def parse_clients(text: str) -> list[Client]:
    clients: list[Client] = []
    for record in split_key_value_lines(text):
        name = record.get("client_name") or record.get("host_name") or record.get("name")
        if name:
            clients.append(client_from_mapping(record | {"name": name}, source="ssh"))
    return clients

