from __future__ import annotations

from nbu.models.jobs import Job, job_from_mapping
from nbu.parsers.common import split_csvish, split_key_value_lines


def parse(text: str) -> list[Job]:
    records = split_key_value_lines(text)
    if records:
        return [
            job_from_mapping(record, source="ssh")
            for record in records
            if record.get("job_id") or record.get("jobid") or record.get("id")
        ]
    jobs: list[Job] = []
    for row in split_csvish(text):
        if len(row) < 4:
            continue
        payload = {
            "job_id": row[0],
            "type": row[1] if len(row) > 1 else None,
            "state": row[2] if len(row) > 2 else None,
            "status": row[3] if len(row) > 3 else None,
            "policy": row[4] if len(row) > 4 else None,
            "client": row[5] if len(row) > 5 else None,
        }
        jobs.append(job_from_mapping(payload, source="ssh"))
    return jobs
