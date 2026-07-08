# netbackup-py

`netbackup-py` est un module Python leger pour automatiser NetBackup avec l'API REST.
Le package s'importe avec `nbu`.

Le module est volontairement concentre sur le noyau utile en production:

- jobs
- policies
- clients issus des details de policies
- schedules issus des details de policies
- images/catalog
- SLP
- appels API directs pour tester un endpoint non encore modele

Il n'y a pas de SSH.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Ou:

```bash
pip install -r requirements.txt
```

## Connexion

```python
from nbu import NetBackup

with NetBackup(
    master="master.company.com",
    username="admin",
    password="password",
    domain_type="unixpwd",
    domain_name="master.company.com",
    version="11.2",
    verify_ssl=False,
) as nb:
    print(nb.ping())
```

Depuis les variables d'environnement:

```bash
export NBU_MASTER=master.company.com
export NBU_USERNAME=admin
export NBU_PASSWORD=password
export NBU_DOMAIN_TYPE=unixpwd
export NBU_DOMAIN_NAME=master.company.com
export NBU_VERSION=11.2
export NBU_VERIFY_SSL=false
```

```python
nb = NetBackup.from_env()
```

## Jobs

Dernieres 24h:

```python
jobs = nb.list_jobs_last_24h(limit=1000)
```

Derniere heure:

```python
jobs = nb.list_jobs_last_hour()
```

Jobs en cours uniquement:

```python
jobs = nb.list_running_jobs(last_hours=1)
```

Jobs termines uniquement:

```python
jobs = nb.list_finished_jobs(last_hours=24)
```

Filtres classiques:

```python
jobs = nb.list_jobs(
    start_date="2026-07-08T00:00:00Z",
    end_date="2026-07-08T23:59:59Z",
    status=0,
    policy="linux-prod",
    client="app01",
    type="BACKUP",
)
```

`date_field` vaut `startTime` par defaut. Vous pouvez utiliser `endTime` ou `lastUpdateTime`:

```python
jobs = nb.list_jobs(date_field="endTime", last_hours=24)
```

Pour les gros volumes:

```python
for job in nb.iter_jobs(last_hours=24, limit=10000):
    print(job.job_id, job.client, job.policy, job.state, job.status)
```

## Policies, Clients Et Schedules

Liste simple des policies:

```python
policies = nb.list_policies(limit=100)
```

Details avec clients, schedules et backup selections:

```python
policies = nb.list_policies(include_details=True)

for policy in policies:
    print(policy.name, policy.policy_type, policy.active)
    print(policy.clients)
    for schedule in policy.schedules:
        print(schedule.schedule_name, schedule.schedule_type, schedule.backup_type)
        print(schedule.retention)
        print(schedule.include_dates, schedule.exclude_dates, schedule.start_window)
        print(schedule.storage, schedule.storage_is_slp, schedule.slp)
```

Une policy precise:

```python
policy = nb.get_policy("linux-prod")
print(policy.clients)
print(policy.schedules)
print(policy.backup_selections)
```

Si `policy.storage_is_slp` ou `schedule.storage_is_slp` vaut `True`, `get_policy()` lit la SLP et
remplace directement:

- `retention`
- `storage`

Donc `schedule.retention` et `schedule.storage` contiennent les valeurs finales quand la SLP est
lisible. `schedule.slp` garde le nom de la SLP utilisee.

Liste des clients proteges, reconstruite uniquement depuis les details des policies:

```python
clients = nb.list_policy_clients()
```

`list_protected_clients()` est un alias.

## Images / Catalog

Dernieres 24h:

```python
images = nb.list_images_last_24h(limit=1000)
```

Derniere heure:

```python
images = nb.list_images_last_hour(client="app01")
```

Avec filtres:

```python
images = nb.list_images(
    client="app01",
    policy="linux-prod",
    start_date="2026-07-08T00:00:00Z",
    end_date="2026-07-08T23:59:59Z",
)
```

Detail d'une image:

```python
image = nb.get_image("app01_1234567890")
```

Contenu catalogue:

```python
contents = nb.list_image_contents(
    filter="backupId eq 'app01_1234567890'",
    limit=100,
)
```

## SLP

```python
slps = nb.list_slps()
slp = nb.get_slp("gold-copy")
```

## Filtres Custom

Tous les endpoints de liste gardes acceptent `filter=` pour envoyer un filtre OData custom.
Le filtre custom est combine avec les raccourcis:

```python
jobs = nb.list_jobs(
    filter="status eq 0",
    policy="linux-prod",
    last_hours=24,
)

images = nb.list_images(
    filter="scheduleType eq 'FULL'",
    client="app01",
    last_hours=24,
)
```

## Pagination

Les methodes `list_*` collectent toutes les pages, sauf si vous passez `limit=`.
Pour eviter de charger trop de donnees, utilisez `iter_jobs()` ou `iter_images()`.

Pour exposer votre propre API paginee:

```python
page = nb.api.get_collection_page(
    "/admin/jobs",
    pagination="cursor",
    page_token=request.args.get("next"),
)

response = {
    "items": page.items,
    "next": page.next_token,
    "total": page.total,
}
```

NetBackup ne retourne pas toujours `total`. Le plus fiable est de suivre `next`.

## Appels API Directs

Pour tester un endpoint non modele, utilisez la session authentifiee:

```python
data = nb.api_get(
    "/config/workloads/vmware/test-query/query-1",
    params={"include": "assets"},
)
```

POST direct:

```python
body = {
    "data": {
        "type": "intelligentTestQueryRequest",
        "attributes": {
            "testQuery": "vcenter Equal 'vc01'",
            "discoveryHost": "media01",
        },
    }
}

result = nb.api_post(
    "/config/workloads/vmware/test-query",
    json=body,
    api_version="14.0",
)
```

Autre methode HTTP:

```python
result = nb.api_request("PUT", "/config/example", json={"data": {"attributes": {}}})
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
nb.collect("images_last_24h")
nb.collect("slp")
```

## Fonctions Principales

- `login()`
- `ping()`
- `discover_version()`
- `api_request()`
- `api_get()`
- `api_post()`
- `list_jobs()`
- `iter_jobs()`
- `list_recent_jobs()`
- `list_jobs_last_24h()`
- `list_jobs_last_hour()`
- `list_running_jobs()`
- `list_finished_jobs()`
- `get_job()`
- `get_job_progress_logs()`
- `list_policies()`
- `get_policy()`
- `list_policy_clients()`
- `list_protected_clients()`
- `list_images()`
- `iter_images()`
- `list_recent_images()`
- `list_images_last_24h()`
- `list_images_last_hour()`
- `get_image()`
- `list_image_contents()`
- `get_image_contents_result()`
- `list_slps()`
- `get_slp()`
- `collect()`
- `close()`
