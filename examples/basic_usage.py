from nbu import NetBackup


with NetBackup(
    master="master.company.com",
    username="user",
    password="password",
    domain_type="unixpwd",
    domain_name="master.company.com",
    version="11.2",
    verify_ssl=False,
) as nb:
    print(nb.ping())

    for job in nb.iter_jobs(start_date="2026-07-01", end_date="2026-07-02", limit=100):
        print(job.job_id, job.client, job.policy, job.status)

