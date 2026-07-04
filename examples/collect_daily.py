from nbu import NetBackup


nb = NetBackup(master="master.company.com", username="user", password="password", version="10.3")
result = nb.collect("jobs", start_date="2026-07-01", end_date="2026-07-02", mode="api")

for document in result.to_indexable():
    print(document)
