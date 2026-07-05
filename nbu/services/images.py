from __future__ import annotations

from nbu.filters import combine, expr, raw_expr
from nbu.models.images import Image
from nbu.parsers.images import parse_image
from nbu.services.base import ServiceBase


class ImagesService(ServiceBase):
    def list(
        self,
        *,
        client: str | None = None,
        policy: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        filter: str | None = None,
        limit: int | None = None,
    ) -> list[Image]:
        return list(
            self.iter(
                client=client,
                policy=policy,
                start_date=start_date,
                end_date=end_date,
                filter=filter,
                limit=limit,
            )
        )

    def iter(
        self,
        *,
        client: str | None = None,
        policy: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        filter: str | None = None,
        limit: int | None = None,
    ):
        self.version.require("images")
        filter_value = combine(
            filter,
            expr("clientName", "eq", client) if client else None,
            expr("policyName", "eq", policy) if policy else None,
            raw_expr("backupTime", "ge", start_date) if start_date else None,
            raw_expr("backupTime", "le", end_date) if end_date else None,
        )
        params = self._drop_none({"filter": filter_value})
        for item in self.api.iter_collection(self.version.endpoint("images"), params, limit=limit):
            yield parse_image(item)

    def get(self, backup_id: str) -> Image:
        self.version.require("images")
        return parse_image(
            self.api.request("GET", self.version.endpoint("image", backup_id=backup_id))
        )

    def contents(
        self,
        *,
        filter: str,
        sort: str | None = None,
        all_copies: bool = False,
        limit: int | None = None,
    ) -> list[dict]:
        self.version.require("images")
        headers = {"X-NetBackup-All-Copies": "true"} if all_copies else None
        params = self._drop_none({"filter": filter, "sort": sort})
        return self.api.get_collection(
            self.version.endpoint("image_contents"),
            params,
            limit=limit,
            headers=headers,
        )

    def contents_result(self, request_id: str) -> list[dict]:
        self.version.require("images")
        return self.api.get_collection(
            self.version.endpoint("image_contents_request", request_id=request_id),
            paginate=False,
        )
