from __future__ import annotations

from nbu.config import CollectionMode
from nbu.filters import combine, expr
from nbu.models.images import Image, image_from_mapping
from nbu.parsers import bpimagelist
from nbu.services.base import ServiceBase


class ImagesService(ServiceBase):
    def list(
        self,
        *,
        mode: CollectionMode | None = None,
        client: str | None = None,
        policy: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
    ) -> list[Image]:
        if self._mode(mode) == "ssh":
            args = []
            if client:
                args.extend(["-client", client])
            if policy:
                args.extend(["-policy", policy])
            images = bpimagelist.parse(self.ssh.run("bpimagelist", *args))
            filtered = [
                image
                for image in images
                if (client is None or image.client == client) and (policy is None or image.policy == policy)
            ]
            return filtered[:limit] if limit is not None else filtered
        return list(
            self.iter(
                mode=mode,
                client=client,
                policy=policy,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )
        )

    def iter(
        self,
        *,
        mode: CollectionMode | None = None,
        client: str | None = None,
        policy: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
    ):
        if self._mode(mode) == "ssh":
            for image in self.list(
                mode="ssh",
                client=client,
                policy=policy,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            ):
                yield image
            return
        self.version.require("images")
        filter_value = combine(
            expr("clientName", "eq", client) if client else None,
            expr("policyName", "eq", policy) if policy else None,
            expr("backupTime", "ge", start_date) if start_date else None,
            expr("backupTime", "le", end_date) if end_date else None,
        )
        params = self._drop_none({"filter": filter_value})
        for item in self.api.iter_collection(self.version.endpoint("images"), params, limit=limit):
            yield image_from_mapping(item)
