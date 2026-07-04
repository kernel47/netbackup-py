from nbu import NetBackup


nb = NetBackup(master="master.company.com", username="user", password="password", version="10.3")
health = nb.health_report()
print(health.model_dump_json(indent=2))
