from nbu import NetBackup


with NetBackup.from_env() as nb:
    for job in nb.iter_jobs(
        start_date="2026-07-01T00:00:00Z",
        end_date="2026-07-02T00:00:00Z",
    ):
        print(job.model_dump(mode="json"))

    for image in nb.iter_images(client="app01", limit=1000):
        print(image.model_dump(mode="json"))
