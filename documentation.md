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
    print(schedule.backup_copies)
    print(schedule.frequency_seconds, schedule.include_dates, schedule.exclude_dates)
    print(schedule.start_window, schedule.storage_is_slp)
```

Les valeurs declarees par le serveur sont conservees. `get_policy()` ne lit pas de SLP
par defaut et ne remplace jamais `storage` ou `retention` par des valeurs issues d'une SLP.

```python
policy = nb.get_policy("linux-prod")
original_json = policy.raw  # reponse API complete, champs inconnus inclus
data = policy.model_dump()  # dictionnaire Python
json_text = policy.model_dump(mode="json", indent=2)  # chaine JSON formatee

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

Les schedules de l'objet de base sont simplifies : nom, type, type de sauvegarde,
frequence, fenetres, dates incluses/exclues, indicateur SLP et `backup_copies`.
`backup_copies` conserve toutes les copies, priorites, strategies d'echec et retentions
sous leur forme API, sans conversion ni selection d'une copie arbitraire.
Les raccourcis `schedule.storage`, `schedule.retention` et `schedule.slp` sont supprimes.
Les options secondaires et les schedules originaux complets restent dans `policy.raw`.
Aucun `raw` n'est ajoute au schedule simplifie et aucun stockage herite n'y est invente.
Une SLP ne recoit pas de retention ou destination globale calculee depuis sa premiere operation.

Chaque ressource conserve des champs utiles et un seul `raw` avec la reponse API complete.
Les schedules et operations SLP imbriques ne dupliquent pas `raw`. Les definitions SLP ajoutees
par `resolve_slp=True` sont des details structures ; une SLP lue directement conserve son propre
`raw`. Les champs propres aux workloads et non exposes par le modele restent dans `raw`.

`model_dump()` (ou `mode="python"`) retourne un dictionnaire Python.
`model_dump(mode="json", indent=2)` retourne une chaine JSON, avec les dates serialisees.
Le parametre `indent` est reserve au mode JSON. `include`, `exclude`, `by_alias` et
`exclude_none` restent disponibles. Par exemple, `exclude={"raw"}` exporte seulement la
structure utile. La serialisation passe uniquement par `model_dump()`.
Modifier un export ne modifie pas le JSON original conserve dans `raw`.

Migration : parcourir `schedule.backup_copies["copies"]` pour lire les stockages
et retentions declares. La resolution SLP doit etre explicitement demandee et ses valeurs
restent dans `policy.slps`.

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
`raw`, sans modifier les reponses recues. Les alias historiques restent
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
