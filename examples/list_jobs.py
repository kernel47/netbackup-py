from nbu import NetBackup


with NetBackup(
    master="master.company.com",
    username="user",
    password="password",
    version="10.3",
) as nb:
    for job in nb.list_jobs(mode="api", ignore_child_jobs=True):
        print(job.model_dump(mode="json"))
