from __future__ import annotations

from nbu.models.base import NbuModel


class VMwareSelection(NbuModel):
    raw: str
    query_filter: str


class VMwareClient(NbuModel):
    name: str
    id: str | None = None


class VMwareTestQuery(NbuModel):
    test_query_id: str
    done: bool | None = None
