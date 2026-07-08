# Documentation netbackup-py

Ce module est maintenant volontairement simple et API-only.

Perimetre garde:

- jobs
- policies
- clients issus des details de policies
- schedules issus des details de policies
- images/catalog
- SLP
- appels API directs

Tout le reste peut etre teste avec `api_get`, `api_post` ou `api_request` avant d'etre ajoute
proprement au module.

## Connexion

```python
from nbu import NetBackup

with NetBackup.from_env() as nb:
    print(nb.ping())
```

Variables utiles:

```bash
export NBU_MASTER=master.company.com
export NBU_USERNAME=admin
export NBU_PASSWORD=password
export NBU_DOMAIN_TYPE=unixpwd
export NBU_DOMAIN_NAME=master.company.com
export NBU_VERSION=11.2
export NBU_VERIFY_SSL=false
```

## Jobs

Dernieres 24h:

```python
jobs = nb.list_jobs_last_24h()
```

Derniere heure:

```python
jobs = nb.list_jobs_last_hour()
```

En cours uniquement:

```python
jobs = nb.list_running_jobs(last_hours=1)
```

Termines uniquement:

```python
jobs = nb.list_finished_jobs(last_hours=24)
```

Filtres:

```python
jobs = nb.list_jobs(
    last_hours=24,
    status=0,
    policy="linux-prod",
    client="app01",
    type="BACKUP",
)
```

Dates explicites:

```python
jobs = nb.list_jobs(
    start_date="2026-07-08T00:00:00Z",
    end_date="2026-07-08T23:59:59Z",
)
```

Changer le champ date:

```python
jobs = nb.list_jobs(date_field="endTime", last_hours=24)
```

Streaming:

```python
for job in nb.iter_jobs(last_hours=24, limit=10000):
    print(job.job_id, job.client, job.policy, job.state, job.status)
```

## Policies

Liste:

```python
policies = nb.list_policies()
```

Details:

```python
policies = nb.list_policies(include_details=True)
```

Une policy:

```python
policy = nb.get_policy("linux-prod")
```

Dans les details de policy, le parser remplit:

- `policy.clients`
- `policy.schedules`
- `policy.backup_selections`
- `policy.storage`
- `policy.retention`

## Clients Proteges

Il n'y a plus d'appel direct `/config/hosts` dans le module.

La liste des clients proteges est reconstruite depuis les details des policies:

```python
clients = nb.list_policy_clients()
```

Alias:

```python
clients = nb.list_protected_clients()
```

Pour VMware, si la policy utilise une selection dynamique, le champ `clients` peut etre vide.
Dans ce cas, utilisez `backup_selections` ou `api_post()` pour tester l'endpoint workload NetBackup.

## Schedules

Les schedules sont dans les details de policy:

```python
policy = nb.get_policy("linux-prod")

for schedule in policy.schedules:
    print(schedule.schedule_name, schedule.schedule_type, schedule.backup_type)
    print(schedule.retention)
    print(schedule.frequency_seconds, schedule.include_dates, schedule.exclude_dates)
    print(schedule.start_window, schedule.storage, schedule.storage_is_slp, schedule.slp)
```

Si `storageIsSLP=True`, `get_policy()` lit la SLP et remplace directement `retention`
et `storage` avec les valeurs finales trouvees dans `operationList` / `operations`.

## Images

Dernieres 24h:

```python
images = nb.list_images_last_24h()
```

Derniere heure:

```python
images = nb.list_images_last_hour(client="app01")
```

Filtres:

```python
images = nb.list_images(
    client="app01",
    policy="linux-prod",
    last_hours=24,
)
```

Detail:

```python
image = nb.get_image("app01_1234567890")
```

Contenu:

```python
contents = nb.list_image_contents(filter="backupId eq 'app01_1234567890'", limit=100)
```

## SLP

```python
slps = nb.list_slps()
slp = nb.get_slp("gold-copy")
```

## Filtres Custom

```python
jobs = nb.list_jobs(filter="status eq 0", last_hours=24)
images = nb.list_images(filter="scheduleType eq 'FULL'", client="app01", last_hours=24)
policies = nb.list_policies(filter="active eq true")
```

## Pagination

Les methodes `list_*` suivent la pagination NetBackup automatiquement.
Ajoutez `limit=` pour borner le nombre de resultats.

Pour exposer une API paginee:

```python
page = nb.api.get_collection_page(
    "/admin/jobs",
    pagination="cursor",
    page_token=request.args.get("next"),
)
```

Retour conseille:

```python
{
    "items": page.items,
    "next": page.next_token,
    "total": page.total,
}
```

`total` peut etre `None`; suivez `next`.

## Appels API Directs

GET:

```python
data = nb.api_get("/config/policies", params={"page[limit]": 10})
```

POST:

```python
body = {
    "data": {
        "type": "intelligentTestQueryRequest",
        "attributes": {"testQuery": "vcenter Equal 'vc01'"},
    }
}

result = nb.api_post("/config/workloads/vmware/test-query", json=body, api_version="14.0")
```

Generique:

```python
result = nb.api_request("DELETE", "/config/example/resource")
```

## Collectors

```python
nb.collect("jobs", last_hours=24)
nb.collect("jobs_last_24h")
nb.collect("jobs_last_hour")
nb.collect("running_jobs", last_hours=1)
nb.collect("finished_jobs", last_hours=24)
nb.collect("policies", include_details=True)
nb.collect("policy_clients")
nb.collect("images", last_hours=24)
nb.collect("images_last_24h")
nb.collect("images_last_hour")
nb.collect("slp")
```

## Fonctions Disponibles

- `api_request`
- `api_get`
- `api_post`
- `list_jobs`
- `iter_jobs`
- `list_recent_jobs`
- `list_jobs_last_24h`
- `list_jobs_last_hour`
- `list_running_jobs`
- `list_finished_jobs`
- `get_job`
- `get_job_progress_logs`
- `list_policies`
- `get_policy`
- `list_policy_clients`
- `list_protected_clients`
- `list_images`
- `iter_images`
- `list_recent_images`
- `list_images_last_24h`
- `list_images_last_hour`
- `get_image`
- `list_image_contents`
- `get_image_contents_result`
- `list_slps`
- `get_slp`
- `collect`
- `discover_version`
- `ping`
- `login`
- `close`
