from __future__ import annotations

from typing import Any

from nbu.config import CollectionMode
from nbu.filters import combine, expr
from nbu.models.jobs import Job, job_from_mapping
from nbu.parsers import bpdbjobs
from nbu.services.base import ServiceBase


class JobsService(ServiceBase):
    def list(
        self,
        *,
        mode: CollectionMode | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        status: int | str | None = None,
        type: str | None = None,
        policy: str | None = None,
        client: str | None = None,
        parent_job_id: int | str | None = None,
        ignore_child_jobs: bool = False,
        limit: int | None = None,
    ) -> list[Job]:
        if self._mode(mode) == "ssh":
            args = ["-most_columns"]
            filtered = self._filter(
                bpdbjobs.parse(self.ssh.run("bpdbjobs", *args)),
                status=status,
                type=type,
                policy=policy,
                client=client,
                parent_job_id=parent_job_id,
                ignore_child_jobs=ignore_child_jobs,
            )
            return filtered[:limit] if limit is not None else filtered
        return list(
            self.iter(
                mode=mode,
                start_date=start_date,
                end_date=end_date,
                status=status,
                type=type,
                policy=policy,
                client=client,
                parent_job_id=parent_job_id,
                ignore_child_jobs=ignore_child_jobs,
                limit=limit,
            )
        )

    def iter(
        self,
        *,
        mode: CollectionMode | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        status: int | str | None = None,
        type: str | None = None,
        policy: str | None = None,
        client: str | None = None,
        parent_job_id: int | str | None = None,
        ignore_child_jobs: bool = False,
        limit: int | None = None,
    ):
        if self._mode(mode) == "ssh":
            for job in self.list(
                mode="ssh",
                start_date=start_date,
                end_date=end_date,
                status=status,
                type=type,
                policy=policy,
                client=client,
                parent_job_id=parent_job_id,
                ignore_child_jobs=ignore_child_jobs,
                limit=limit,
            ):
                yield job
            return
        self.version.require("jobs")
        filter_value = combine(
            expr("startTime", "ge", start_date) if start_date else None,
            expr("endTime", "le", end_date) if end_date else None,
            expr("status", "eq", status) if status is not None else None,
            expr("jobType", "eq", type) if type else None,
            expr("policyName", "eq", policy) if policy else None,
            expr("clientName", "eq", client) if client else None,
            expr("parentJobId", "eq", parent_job_id) if parent_job_id is not None else None,
        )
        params = self._drop_none({"filter": filter_value, "sort": "-startTime"})
        yielded = 0
        for item in self.api.iter_collection(
            self.version.endpoint("jobs"),
            params,
            pagination="cursor",
            limit=limit,
        ):
            job = job_from_mapping(item)
            if ignore_child_jobs and job.parent_job_id:
                continue
            yielded += 1
            yield job
            if limit is not None and yielded >= limit:
                break

    def get(self, job_id: int | str, *, mode: CollectionMode | None = None) -> Job:
        if self._mode(mode) == "ssh":
            matches = [job for job in self.list(mode="ssh") if str(job.job_id) == str(job_id)]
            if not matches:
                from nbu.exceptions import NotFoundError

                raise NotFoundError(f"Job {job_id!r} was not found")
            return matches[0]
        self.version.require("jobs")
        return job_from_mapping(self.api.request("GET", self.version.endpoint("job", job_id=job_id)))

    @staticmethod
    def _filter(jobs: list[Job], **criteria: Any) -> list[Job]:
        filtered = jobs
        if criteria.get("ignore_child_jobs"):
            filtered = [job for job in filtered if not job.parent_job_id]
        for field in ("status", "type", "policy", "client", "parent_job_id"):
            value = criteria.get(field)
            if value is not None:
                filtered = [job for job in filtered if str(getattr(job, field)) == str(value)]
        return filtered
