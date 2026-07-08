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
                "jobs_last_24h": self.client.list_jobs_last_24h,
                "jobs_last_hour": self.client.list_jobs_last_hour,
                "running_jobs": self.client.list_running_jobs,
                "finished_jobs": self.client.list_finished_jobs,
                "policies": self.client.list_policies,
                "policy_clients": self.client.list_policy_clients,
                "protected_clients": self.client.list_protected_clients,
                "images": self.client.list_images,
                "images_last_24h": self.client.list_images_last_24h,
                "images_last_hour": self.client.list_images_last_hour,
                "slp": self.client.list_slps,
            }[name]
        except KeyError as exc:
            raise ValueError(f"Unknown collector {name!r}") from exc
        return Collector(self.client, name, loader)

    def collect(self, name: str, **kwargs: Any) -> CollectionResult:
        return self.get(name).collect(**kwargs)

    def jobs(self) -> Collector:
        return self.get("jobs")

    def jobs_last_24h(self) -> Collector:
        return self.get("jobs_last_24h")

    def jobs_last_hour(self) -> Collector:
        return self.get("jobs_last_hour")

    def running_jobs(self) -> Collector:
        return self.get("running_jobs")

    def finished_jobs(self) -> Collector:
        return self.get("finished_jobs")

    def policies(self) -> Collector:
        return self.get("policies")

    def policy_clients(self) -> Collector:
        return self.get("policy_clients")

    def protected_clients(self) -> Collector:
        return self.get("protected_clients")

    def images(self) -> Collector:
        return self.get("images")

    def images_last_24h(self) -> Collector:
        return self.get("images_last_24h")

    def images_last_hour(self) -> Collector:
        return self.get("images_last_hour")

    def slp(self) -> Collector:
        return self.get("slp")
