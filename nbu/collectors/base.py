from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field


class CollectionResult(BaseModel):
    collector: str
    records: list[Any] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_indexable(self) -> list[dict[str, Any]]:
        docs = []
        for record in self.records:
            if hasattr(record, "model_dump"):
                docs.append(record.model_dump(mode="json"))
            else:
                docs.append(dict(record))
        return docs


class Collector:
    """Tiny collector wrapper around a service function."""

    def __init__(self, client: Any, name: str, loader: Callable[..., Any]) -> None:
        self.client = client
        self.name = name
        self._loader = loader

    def collect(self, **kwargs: Any) -> CollectionResult:
        records = self._loader(**kwargs)
        if not isinstance(records, list):
            records = [records]
        return CollectionResult(collector=self.name, records=records, metadata=kwargs)


class Collectors:
    """Convenience factory for daily collection jobs."""

    def __init__(self, client: Any) -> None:
        self.client = client

    def get(self, name: str) -> Collector:
        try:
            loader = {
                "jobs": self.client.list_jobs,
                "policies": self.client.list_policies,
                "clients": self.client.list_clients,
                "images": self.client.list_images,
                "storage": self.client.list_storage,
                "slp": self.client.list_slps,
                "vm": self.client.list_vm_assets,
                "health": self.client.health_report,
            }[name]
        except KeyError as exc:
            raise ValueError(f"Unknown collector {name!r}") from exc
        return Collector(self.client, name, loader)

    def collect(self, name: str, **kwargs: Any) -> CollectionResult:
        return self.get(name).collect(**kwargs)

    def jobs(self) -> Collector:
        return self.get("jobs")

    def policies(self) -> Collector:
        return self.get("policies")

    def clients(self) -> Collector:
        return self.get("clients")

    def images(self) -> Collector:
        return self.get("images")

    def storage(self) -> Collector:
        return self.get("storage")

    def slp(self) -> Collector:
        return self.get("slp")

    def vm(self) -> Collector:
        return self.get("vm")

    def health(self) -> Collector:
        return self.get("health")
