from nbu import NetBackup


with NetBackup(
    master="master.company.com",
    username="user",
    password="password",
    domain_type="unixpwd",
    domain_name="master.company.com",
    version="10.3",
) as nb:
    for job in nb.list_jobs(ignore_child_jobs=True):
        print(job.model_dump(mode="json"))
