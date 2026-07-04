from __future__ import annotations

from nbu.filters import combine, expr, raw_expr
from nbu.models.jobs import Job, job_from_mapping
from nbu.services.base import ServiceBase

JOB_DATE_FIELDS = {"startTime", "endTime", "lastUpdateTime"}


class JobsService(ServiceBase):
    def list(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        date_field: str = "startTime",
        filter: str | None = None,
        status: int | str | None = None,
        type: str | None = None,
        policy: str | None = None,
        client: str | None = None,
        parent_job_id: int | str | None = None,
        ignore_child_jobs: bool = False,
        limit: int | None = None,
    ) -> list[Job]:
        return list(
            self.iter(
                start_date=start_date,
                end_date=end_date,
                date_field=date_field,
                filter=filter,
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
        start_date: str | None = None,
        end_date: str | None = None,
        date_field: str = "startTime",
        filter: str | None = None,
        status: int | str | None = None,
        type: str | None = None,
        policy: str | None = None,
        client: str | None = None,
        parent_job_id: int | str | None = None,
        ignore_child_jobs: bool = False,
        limit: int | None = None,
    ):
        self.version.require("jobs")
        if date_field not in JOB_DATE_FIELDS:
            allowed = ", ".join(sorted(JOB_DATE_FIELDS))
            raise ValueError(f"date_field must be one of: {allowed}")
        filter_value = combine(
            filter,
            raw_expr(date_field, "ge", start_date) if start_date else None,
            raw_expr(date_field, "le", end_date) if end_date else None,
            expr("status", "eq", status) if status is not None else None,
            expr("jobType", "eq", type) if type else None,
            expr("policyName", "eq", policy) if policy else None,
            expr("clientName", "eq", client) if client else None,
            expr("parentJobId", "eq", parent_job_id) if parent_job_id is not None else None,
        )
        params = self._drop_none({"filter": filter_value, "sort": "-startTime"})
        yielded = 0
        api_limit = None if ignore_child_jobs else limit
        for item in self.api.iter_collection(
            self.version.endpoint("jobs"),
            params,
            pagination="cursor",
            limit=api_limit,
        ):
            job = job_from_mapping(item)
            if ignore_child_jobs and job.parent_job_id:
                continue
            yielded += 1
            yield job
            if limit is not None and yielded >= limit:
                break

    def get(self, job_id: int | str) -> Job:
        self.version.require("jobs")
        return job_from_mapping(self.api.request("GET", self.version.endpoint("job", job_id=job_id)))
