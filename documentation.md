# Documentation netbackup-py

`netbackup-py` est un module Python leger pour utiliser l'API REST Veritas NetBackup.
Le package Python s'importe avec `nbu`.

Le module est maintenant 100% API REST. Il ne fait plus de SSH et ne lance plus de commandes
NetBackup comme `bpdbjobs`, `bpimagelist` ou `bppllist`.

## Prerequis

- Python 3.12 ou plus recent
- Acces HTTPS au master NetBackup
- Un compte NetBackup autorise a utiliser l'API REST
- NetBackup 10.0 ou plus recent

## Installation

Depuis le repo:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Ou avec les requirements:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Dependances principales:

- `httpx` pour les appels HTTP
- `pydantic` pour les modeles de donnees

## Connexion

Exemple simple:

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

NetBackup demande souvent `domainType` et `domainName` au login. Le module les envoie dans le
payload `/login`:

```json
{
  "userName": "admin",
  "password": "password",
  "domainType": "unixpwd",
  "domainName": "master.company.com"
}
```

Si votre environnement utilise un compte local sans domaine, vous pouvez laisser
`domain_type=""` et `domain_name=""`.

## Variables d'environnement

Vous pouvez configurer la connexion avec des variables d'environnement:

```bash
export NBU_MASTER=master.company.com
export NBU_USERNAME=admin
export NBU_PASSWORD=password
export NBU_DOMAIN_TYPE=unixpwd
export NBU_DOMAIN_NAME=master.company.com
export NBU_VERSION=11.2
export NBU_VERIFY_SSL=false
```

Puis:

```python
from nbu import NetBackup

with NetBackup.from_env() as nb:
    print(nb.ping())
```

## Versions NetBackup supportees

Le module cible NetBackup 10.0 et plus recent.

La version API est deduite automatiquement quand vous donnez `version=`:

| NetBackup | API media version |
| --- | --- |
| 10.0 | 7.0 |
| 10.1 | 8.0 |
| 10.2 | 9.0 |
| 10.3 | 10.0 |
| 10.4 | 11.0 |
| 11.0 | 13.0 |
| 11.1 | 14.0 |
| 11.2 | 14.0 |

Si votre environnement a une particularite, forcez la version API:

```python
nb = NetBackup(
    master="master.company.com",
    token="TOKEN",
    version="11.2",
    api_version="14.0",
)
```

## Fonctions principales

Le client principal est `NetBackup`.

```python
from nbu import NetBackup

nb = NetBackup(...)
```

Fonctions generales:

| Fonction | Description |
| --- | --- |
| `login()` | Fait le login API et stocke le token |
| `ping()` | Teste `/ping` sur le master NetBackup |
| `discover_version()` | Essaie de detecter la version NetBackup via l'API |
| `close()` | Ferme le client HTTP |

Fonctions de collecte:

| Fonction | Description |
| --- | --- |
| `list_jobs()` | Liste les jobs NetBackup |
| `iter_jobs()` | Stream les jobs un par un |
| `get_job(job_id)` | Recupere un job precis |
| `list_images()` | Liste les images du catalogue |
| `iter_images()` | Stream les images une par une |
| `list_policies()` | Liste les policies |
| `get_policy(policy_name)` | Recupere une policy precise |
| `list_clients()` | Liste les hosts/clients |
| `list_storage()` | Liste storage units et disk pools |
| `list_slps()` | Liste les SLP |
| `list_vm_assets()` | Liste les assets VMware |
| `health_report()` | Retourne un rapport de sante simple |
| `collect(name, **kwargs)` | Collecte generique par nom: `jobs`, `images`, etc. |

## Jobs

Lister les jobs:

```python
jobs = nb.list_jobs()

for job in jobs:
    print(job.job_id, job.client, job.policy, job.status)
```

Filtrer par date:

```python
jobs = nb.list_jobs(
    start_date="2026-07-01T00:00:00Z",
    end_date="2026-07-02T00:00:00Z",
)
```

Par defaut, `start_date` et `end_date` filtrent sur `startTime`:

```text
startTime ge 2026-07-01T00:00:00Z and startTime le 2026-07-02T00:00:00Z
```

Vous pouvez changer le champ date:

```python
jobs = nb.list_jobs(
    date_field="endTime",
    start_date="2026-07-01T00:00:00Z",
    end_date="2026-07-02T00:00:00Z",
)
```

Champs acceptes pour `date_field`:

- `startTime`
- `endTime`
- `lastUpdateTime`

Filtrer par status, policy, client:

```python
jobs = nb.list_jobs(
    status=0,
    policy="linux-prod",
    client="app01",
)
```

Ignorer les child jobs:

```python
jobs = nb.list_jobs(ignore_child_jobs=True)
```

Recuperer un job:

```python
job = nb.get_job(12345)
print(job.raw)
```

## Images catalogue

Lister les images:

```python
images = nb.list_images(client="app01")

for image in images:
    print(image.backup_id, image.client, image.policy, image.backup_time)
```

Filtrer par date de backup:

```python
images = nb.list_images(
    client="app01",
    start_date="2026-07-01T00:00:00Z",
    end_date="2026-07-02T00:00:00Z",
)
```

Filtrer par policy:

```python
images = nb.list_images(policy="linux-prod")
```

## Policies

Lister toutes les policies:

```python
policies = nb.list_policies()
```

Chercher une policy par nom:

```python
policies = nb.list_policies(name="prod")
```

Recuperer une policy precise:

```python
policy = nb.get_policy("linux-prod")
```

## Clients

Lister les clients/hosts:

```python
clients = nb.list_clients()
```

Filtrer par nom:

```python
clients = nb.list_clients(name="app")
```

## Storage

Tout lister:

```python
storage = nb.list_storage()
```

Utiliser les services detailles:

```python
storage_units = nb.storage.storage_units()
disk_pools = nb.storage.disk_pools()
```

Filtrer:

```python
storage_units = nb.storage.storage_units(name="stu-prod")
disk_pools = nb.storage.disk_pools(name="dp-prod")
```

## SLP

Lister les Storage Lifecycle Policies:

```python
slps = nb.list_slps()
```

Filtrer:

```python
slps = nb.list_slps(name="gold")
```

Recuperer une SLP:

```python
slp = nb.slp.get("gold-copy")
```

## VMware assets

Lister les assets VMware:

```python
assets = nb.list_vm_assets()
```

Limiter le nombre de resultats:

```python
assets = nb.list_vm_assets(limit=500)
```

## Health report

Rapport de sante simple:

```python
health = nb.health_report()
print(health.model_dump_json(indent=2))
```

Le rapport teste notamment:

- reachability du master via `/ping`
- disponibilite de l'API
- authentification
- jobs en erreur
- storage
- SLP
- certificats si l'endpoint est disponible

Le statut des processus NetBackup type `bpps` n'est pas collecte, car le module est API-only.

## Pagination

Le module gere automatiquement la pagination NetBackup.

Il y a deux facons de collecter.

### Mode liste

Les fonctions `list_*()` recuperent toutes les pages et retournent une liste Python:

```python
jobs = nb.list_jobs()
images = nb.list_images()
```

Avantage: tres simple.

Attention: si vous avez beaucoup de jobs ou d'images, cela peut charger beaucoup de donnees en
memoire.

Vous pouvez limiter:

```python
jobs = nb.list_jobs(limit=1000)
images = nb.list_images(limit=500)
```

### Mode streaming

Les fonctions `iter_*()` lisent les pages NetBackup mais retournent les objets un par un:

```python
for job in nb.iter_jobs(start_date="2026-07-01T00:00:00Z"):
    print(job.job_id)
```

C'est le mode recommande pour les gros environnements.

### Strategie officielle utilisee

| Ressource | Pagination |
| --- | --- |
| Jobs `/admin/jobs` | Cursor avec `page[after]` |
| Images `/catalog/images` | Offset avec `page[offset]` |
| Policies `/config/policies/` | Offset avec `page[offset]` |
| Clients `/config/hosts` | Offset avec `page[offset]` |
| Storage `/storage/*` | Offset avec `page[offset]` |
| SLP `/config/slps` | Offset avec `page[offset]` |

Le module envoie aussi `page[limit]` selon `page_limit` dans la config.

## Filtres custom

Les endpoints NetBackup utilisent des filtres OData.

Vous pouvez passer un filtre custom avec `filter=`:

```python
jobs = nb.list_jobs(filter="status eq 0 and jobType eq 'BACKUP'")
```

Le filtre custom peut etre combine avec les raccourcis:

```python
jobs = nb.list_jobs(
    filter="status eq 0",
    policy="linux-prod",
    start_date="2026-07-01T00:00:00Z",
    end_date="2026-07-02T00:00:00Z",
)
```

Le module construit:

```text
status eq 0 and startTime ge 2026-07-01T00:00:00Z and startTime le 2026-07-02T00:00:00Z and policyName eq 'linux-prod'
```

Exemples:

```python
jobs = nb.list_jobs(filter="state eq 'DONE' and status ne 0")
images = nb.list_images(filter="scheduleType eq 'FULL'", client="app01")
policies = nb.list_policies(filter="active eq true")
clients = nb.list_clients(filter="contains(hostName,'app')")
```

## Collectors

Les collectors retournent un `CollectionResult`.

Exemple:

```python
result = nb.collect(
    "jobs",
    start_date="2026-07-01T00:00:00Z",
    end_date="2026-07-02T00:00:00Z",
    limit=1000,
)

print(result.collector)
print(result.metadata)

for document in result.to_indexable():
    print(document)
```

Collecteurs disponibles via la facade:

```python
nb.collect("jobs")
nb.collect("images")
nb.collect("policies")
nb.collect("clients")
nb.collect("storage")
nb.collect("slp")
nb.collect("vm")
nb.collect("health")
```

Style fluent:

```python
result = nb.collectors.jobs().collect(status=0, limit=1000)
```

## Modeles retournes

Les objets retournes sont des modeles Pydantic.

Modeles principaux:

- `Job`
- `Image`
- `Policy`
- `Client`
- `StorageUnit`
- `DiskPool`
- `SLP`
- `VMAsset`
- `HealthCheck`
- `HealthReport`

Chaque modele garde le payload original dans `raw`.

Exemple:

```python
job = nb.get_job(12345)
print(job.job_id)
print(job.raw)
```

Convertir en dict JSON-friendly:

```python
payload = job.model_dump(mode="json")
```

## Configuration avancee

Exemple:

```python
nb = NetBackup(
    master="master.company.com",
    username="admin",
    password="password",
    domain_type="unixpwd",
    domain_name="master.company.com",
    version="11.2",
    verify_ssl=True,
    timeout=60,
    retries=5,
    retry_backoff=1.0,
    page_limit=500,
)
```

Parametres utiles:

| Parametre | Description |
| --- | --- |
| `master` | Nom DNS ou IP du master NetBackup |
| `username` | Utilisateur API |
| `password` | Mot de passe API |
| `token` | Token existant, pour eviter le login password |
| `domain_type` | Type de domaine NetBackup, ex: `unixpwd` |
| `domain_name` | Nom du domaine ou master local |
| `version` | Version NetBackup, ex: `11.2` |
| `api_version` | Force la media version API |
| `verify_ssl` | Verification TLS |
| `timeout` | Timeout HTTP |
| `retries` | Nombre de retries HTTP |
| `page_limit` | Taille de page envoyee a l'API |
| `authorization_scheme` | Ex: `Bearer` si votre gateway le demande |
| `extra_headers` | Headers HTTP supplementaires |

## Exemple production pour beaucoup de jobs

```python
from nbu import NetBackup

with NetBackup.from_env() as nb:
    for job in nb.iter_jobs(
        start_date="2026-07-01T00:00:00Z",
        end_date="2026-07-02T00:00:00Z",
        filter="jobType eq 'BACKUP'",
    ):
        document = job.model_dump(mode="json")
        # envoyer document vers fichier, database, Elasticsearch, etc.
        print(document)
```

## Exemple production pour beaucoup d'images

```python
from nbu import NetBackup

with NetBackup.from_env() as nb:
    for image in nb.iter_images(
        client="app01",
        start_date="2026-07-01T00:00:00Z",
        end_date="2026-07-02T00:00:00Z",
        limit=10000,
    ):
        print(image.model_dump(mode="json"))
```

## Bonnes pratiques

- Utiliser `iter_jobs()` et `iter_images()` pour les gros environnements.
- Toujours filtrer par date quand vous collectez beaucoup de jobs ou images.
- Utiliser des dates ISO 8601 completes, par exemple `2026-07-01T00:00:00Z`.
- Utiliser `limit=` pour tester avant de lancer une collecte complete.
- Garder `raw` si vous voulez auditer exactement la reponse NetBackup.
- Forcer `api_version=` seulement si la detection par `version=` ne correspond pas a votre master.

