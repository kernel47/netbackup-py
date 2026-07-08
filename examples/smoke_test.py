from __future__ import annotations

from nbu import NetBackup


def show(name: str, value: object) -> None:
    print(f"\n## {name}")
    print(value)


def main() -> None:
    with NetBackup.from_env() as nb:
        show("ping", nb.ping())

        jobs = nb.list_jobs_last_24h(limit=5)
        show("list_jobs", [job.model_dump(mode="json") for job in jobs])

        if jobs:
            show("get_job", nb.get_job(jobs[0].job_id).model_dump(mode="json"))
            show("get_job_progress_logs", nb.get_job_progress_logs(jobs[0].job_id, limit=5))

        show("iter_jobs", [job.model_dump(mode="json") for job in nb.iter_jobs(limit=5)])
        show(
            "list_running_jobs",
            [job.model_dump(mode="json") for job in nb.list_running_jobs(limit=5)],
        )

        policies = nb.list_policies(limit=5)
        show("list_policies summaries", [policy.model_dump(mode="json") for policy in policies])

        policies_with_details = nb.list_policies(limit=5, include_details=True)
        show(
            "list_policies include_details",
            [policy.model_dump(mode="json") for policy in policies_with_details],
        )

        if policies:
            show("get_policy", nb.get_policy(policies[0].name).model_dump(mode="json"))

        show(
            "list_policy_clients",
            [client.model_dump(mode="json") for client in nb.list_policy_clients(limit=5)],
        )

        images = nb.list_images_last_24h(limit=5)
        show("list_images", [image.model_dump(mode="json") for image in images])
        show("iter_images", [image.model_dump(mode="json") for image in nb.iter_images(limit=5)])
        if images and images[0].backup_id:
            show("get_image", nb.get_image(images[0].backup_id).model_dump(mode="json"))
            show(
                "list_image_contents",
                nb.list_image_contents(filter=f"backupId eq '{images[0].backup_id}'", limit=5),
            )

        slps = nb.list_slps(limit=5)
        show("list_slps", [slp.model_dump(mode="json") for slp in slps])
        if slps:
            show("slp.get", nb.slp.get(slps[0].name).model_dump(mode="json"))

        collected = nb.collect("jobs", limit=5)
        show("collect jobs", collected.model_dump(mode="json"))


if __name__ == "__main__":
    main()
