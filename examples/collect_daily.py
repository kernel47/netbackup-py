from nbu import NetBackup


nb = NetBackup(master="master.company.com", username="user", password="password", version="10.3")
result = nb.collect(
    "jobs",
    start_date="2026-07-01T00:00:00Z",
    end_date="2026-07-02T00:00:00Z",
)

for document in result.to_indexable():
    print(document)
