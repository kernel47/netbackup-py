from nbu import NetBackup


with NetBackup.from_env() as nb:
    for job in nb.iter_jobs(start_date="2026-07-01", end_date="2026-07-02", mode="api"):
        print(job.model_dump(mode="json"))

    for image in nb.iter_images(client="app01", mode="api", limit=1000):
        print(image.model_dump(mode="json"))

