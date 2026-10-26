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

Les valeurs declarees par le serveur sont conservees. `get_policy()` ne lit pas de SLP
par defaut et ne remplace jamais `storage` ou `retention` par des valeurs issues d'une SLP.

```python
policy = nb.get_policy("linux-prod")
original_json = policy.to_api()  # copie du JSON API original, champs inconnus inclus
configuration = policy.configuration  # corps complet de la policy
clients_details = policy.client_details  # OS, hardware, identifiants de bases/instances...

policy = nb.get_policy("linux-prod", resolve_slp=True)
for name, slp in policy.slps.items():
    print(name, slp.version_number)
    for operation in slp.operations:
        print(operation.operation, operation.storage,
              operation.retention_type, operation.retention)
```

`resolve_slp=True` ajoute les definitions SLP dans `policy.slps`, sans modifier la configuration.
Les erreurs de lecture SLP sont propagees. Sur une liste, utiliser
`list_policies(include_details=True, resolve_slp=True)` : les SLP communes sont lues une seule
fois pendant la collecte. Le GET SLP retourne la definition courante, pas la configuration
historique d'une image deja sauvegardee.

`backup_copies` conserve l'objet API complet : `copies`, `priority`, `failStrategy`, niveaux
et periodes de retention. `retention` conserve sa structure `{value, unit}` ou son niveau
numerique si seule cette information est disponible. Aucun niveau n'est transforme en duree.
Les raccourcis `schedule.storage` et `schedule.retention` ne resument les copies que si leurs
valeurs sont identiques ; sinon ils valent `None`. Un stockage absent du schedule n'est pas
remplace par celui de la policy. Il faut consulter les deux niveaux pour analyser l'heritage.
Une SLP ne recoit pas de retention ou destination globale calculee depuis sa premiere operation.

Tous les modeles issus des parsers proposent `to_api()` et `api_attributes`. `to_api()` retourne
une copie du JSON recu, sans champs calcules ; `model_dump()` retourne la vue Python du modele.
Modifier une vue ou un export ne modifie pas le JSON original conserve dans `raw`.

Migration : `schedule.retention` n'est plus une chaine telle que `"14 DAYS"` et
`backup_copies` n'est plus le dictionnaire de la seule premiere copie. Utiliser
`schedule.backup_copies["copies"]` pour parcourir les copies. La resolution SLP doit etre
explicitement demandee et ses valeurs restent dans `policy.slps`.

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

## Versions API

Le module distingue la release NetBackup du contrat API. Correspondances par defaut :
10.0 -> 7.0, 10.1 -> 8.0, 10.1.1 -> 9.0, 10.2 -> 9.0, 10.3 -> 10.0,
10.4 -> 11.0, 10.5 -> 12.0, 11.0 -> 13.0, 11.1 et 11.2 -> 14.0.
Les correctifs d'une release suivent son contrat ; 10.1.1 est traite avant 10.1.
Une release inconnue necessite `api_version=` explicite. Sans release ni version API,
le comportement historique utilise 7.0 ; renseigner `version=` pour un serveur recent.

Une surcharge globale `api_version=` ou par service reste possible :

```python
nb = NetBackup(master="master.company.com", token="...", version="11.1",
               api_versions={"config_policies": "14.0", "config_slp": "14.0"})
```

La pagination policies 14.0 reste basee sur les offsets et prend en charge `hasNext`.
Un compteur de page `count` n'est pas presente comme un total de collection.
Les anciennes versions API peuvent etre depreciees par le serveur ; le module ne garantit
pas qu'un contrat ancien reste accepte sur toutes les releases recentes.

Sources : [Getting Started 11.1](https://sort.veritas.com/public/documents/nbu/11.1/windowsandunix/productguides/html/getting-started/),
[Policies 11.1](https://sort.veritas.com/public/documents/nbu/11.1/windowsandunix/productguides/html/config_policies/config_policies.yaml)
et [Configuration / SLP 11.1](https://sort.veritas.com/public/documents/nbu/11.1/windowsandunix/productguides/html/config/config.yaml).

## Parsers jobs et images : fidelite aux donnees API

Les contrats officiels Administration et Catalog des releases 10.0, 10.1.1, 10.5, 11.1
et 11.2 ont ete compares pour ces champs. Les parsers conservent les champs inconnus dans
`raw` et `api_attributes`, sans modifier les reponses recues. Les alias historiques restent
acceptes lorsqu'un champ officiel est absent ; une valeur officielle `null`, vide ou zero
n'est pas remplacee par un alias.

Pour les jobs :

- `files` lit `numberOfFiles`.
- `elapsed_time` et `active_elapsed_time` gardent les chaines API originales. Les anciens
  contrats utilisent notamment `hh:mm:ss`, et le contrat 9.0 (NetBackup 10.1.1) utilise des
  durees ISO 8601. Aucune conversion implicite en secondes n'est effectuee ;
  `elapsed_seconds` ne lit que les anciens champs explicites en secondes.
- `source_storage_unit` et `destination_storage_unit` restent distincts.
  `storage_unit` ne choisit pas arbitrairement l'un des deux.
- `kilobytes` correspond a `kilobytesTransferred` (estimation selon le schema), tandis que
  `kilobytes_data_transferred` et `kilobytes_to_transfer` exposent leurs champs respectifs.
- `last_update_time` expose `lastUpdateTime` ; l'identifiant et les compteurs zero sont conserves.

Pour les images :

- `kilobytes` lit `kbytes` ; `expiration_time` lit `expiration`. Une expiration `null`
  reste `None`, notamment pour une image sans expiration.
- `fragments` conserve tous les fragments de toutes les copies, leurs champs et extensions.
- `primary_copy`, `num_copies`, `num_files`, `elapsed_seconds`, `slp_name` et `slp_version`
  exposent les valeurs correspondantes. Aucun appel SLP n'est ajoute.
- `primary_copy` ne remplace pas `copy_number`. Aucun stockage ou expiration d'un fragment
  n'est presente arbitrairement comme une valeur pour l'image entiere.

```python
job = nb.get_job(123)
print(job.files, job.elapsed_time)
print(job.source_storage_unit, job.destination_storage_unit)

image = nb.get_image("app01_1234567890")
print(image.kilobytes, image.expiration_time, image.primary_copy)
for fragment in image.fragments:
    print(fragment.get("copyNumber"), fragment.get("mediaId"), fragment.get("expiration"))

original_json = image.raw  # acces direct toujours disponible
```

Sources officielles :
[Administration 11.1](https://sort.veritas.com/public/documents/nbu/11.1/windowsandunix/productguides/html/admin/admin.yaml),
[Catalog 11.1](https://sort.veritas.com/public/documents/nbu/11.1/windowsandunix/productguides/html/catalog/catalog.yaml),
[Administration 10.0](https://sort.veritas.com/public/documents/nbu/10.0/windowsandunix/productguides/html/admin/admin.yaml)
et [Administration 10.1.1](https://sort.veritas.com/public/documents/nbu/10.1.1/windowsandunix/productguides/html/admin/admin.yaml).

Les tests couvrent des reponses de liste et de detail, les durees anciennes et ISO,
les valeurs zero/null, les copies multiples et l'isolation de `raw`. Ils ne remplacent
pas une validation sur un serveur reel.
