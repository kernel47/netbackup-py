# netbackup-py

`netbackup-py` provides a modern typed Python REST API wrapper for Veritas NetBackup automation,
collection, health checks, and reporting. It is intentionally NetBackup-oriented and exposes the
import package as `nbu`.

The library targets NetBackup 10.0 and newer. REST endpoint mappings are centralized in
`nbu.version.VersionManager` so deployments can adapt paths as Veritas evolves the OpenAPI
specification exposed by each master server.

The current mappings were checked against the official Veritas SORT Swagger/OpenAPI references for
NetBackup 10.0 and 11.2:

- NetBackup Authentication API: `gateway.yaml`
- NetBackup Administration API: `admin.yaml`
- NetBackup Catalog API: `catalog.yaml`
- NetBackup Configuration API: `config.yaml`
- NetBackup Storage API: `storage.yaml`
- NetBackup Hosts Configuration API: `config_hosts.yaml`

Your master server may also expose matching API documentation at
`https://<master>/api-docs/index.html`.

## Install

Recommended editable install for development:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Classic requirements install:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Development dependencies:

```bash
pip install -r requirements-dev.txt
```

Because this is a package, `pyproject.toml` is the main dependency definition. The
`requirements*.txt` files are provided for simple deployments and scripts.

## Quick Start

Create a file, for example `my_nbu_script.py`:

```python
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

    jobs = nb.list_jobs(
        start_date="2026-07-01T00:00:00Z",
        end_date="2026-07-02T00:00:00Z",
        limit=100,
    )
    for job in jobs:
        print(job.job_id, job.client, job.policy, job.status)
```

Run it:

```bash
python my_nbu_script.py
```

For day-to-day scripts, use the shorter facade methods:

```python
jobs = nb.list_jobs(status=0, policy="linux-prod")
images = nb.list_images(
    client="app01",
    start_date="2026-07-01T00:00:00Z",
    end_date="2026-07-02T00:00:00Z",
)
storage = nb.list_storage()
health = nb.health_report()
```

You can also load connection settings from environment variables:

```bash
export NBU_MASTER=master.company.com
export NBU_USERNAME=user
export NBU_PASSWORD=password
export NBU_DOMAIN_TYPE=unixpwd
export NBU_DOMAIN_NAME=master.company.com
export NBU_VERSION=11.2
```

```python
nb = NetBackup.from_env()
```

Automatic version discovery is available when the master exposes version information:

```python
version = nb.discover_version()
print(nb.version.current)
```

## API Login

The client uses the NetBackup REST API with token login, NetBackup vendor media headers,
domain-aware authentication, pagination, retries, timeouts, SSL verification configuration, and
optional proxy settings.

For login, NetBackup commonly expects:

```json
{
  "userName": "user",
  "password": "password",
  "domainType": "unixpwd",
  "domainName": "master.company.com"
}
```

`domain_type` and `domain_name` default to empty strings for local accounts, matching the
classic `nbupy` behavior. The library sends `Accept` and `Content-Type` as
`application/vnd.netbackup+json;version=<api_version>` and sends the NetBackup token as the raw
`Authorization` header value by default. Set `authorization_scheme="Bearer"` only if your API
gateway or environment requires it.

Paginated collection calls automatically send `page[limit]` and follow the official pagination
metadata until all pages are collected. Jobs use cursor pagination with `page[after]`; catalog,
configuration, SLP, and storage collections use offset pagination with `page[offset]`.

If you build your own API on top of this package, use `nb.api.get_collection_page(...)` and expose
`next_token` to callers. NetBackup does not always return a total count, so `total` is optional.
The client also supports per-area media versions through `api_versions`; this is used for 11.x
policy endpoints where `config_policies.yaml` advertises a different media version than admin or
catalog.

## Large Collections

By default, list methods collect every page that NetBackup returns:

```python
jobs = nb.list_jobs(start_date="2026-07-01T00:00:00Z", end_date="2026-07-02T00:00:00Z")
images = nb.list_images(client="app01")
```

That is convenient for small result sets, but it can load many records into memory. Use `limit`
when you only need a bounded result:

```python
jobs = nb.list_jobs(status=0, limit=1000)
images = nb.list_images(client="app01", limit=500)
```

For large environments, stream records instead:

```python
for job in nb.iter_jobs(start_date="2026-07-01T00:00:00Z", end_date="2026-07-02T00:00:00Z"):
    process(job)

for image in nb.iter_images(client="app01", limit=10_000):
    process(image)
```

Streaming still follows NetBackup pagination, but it yields records one by one instead of building
one large list first. The safest production pattern is to combine streaming with date filters.

Dates should be ISO 8601 values accepted by the NetBackup API. They are sent as date-time values
inside the OData filter, for example `startTime ge 2026-07-01T00:00:00Z`.

Jobs default to filtering on `startTime`:

```python
jobs = nb.list_jobs(
    start_date="2026-07-01T00:00:00Z",
    end_date="2026-07-02T00:00:00Z",
)
```

You can switch the job date field when needed:

```python
jobs = nb.list_jobs(
    date_field="endTime",
    start_date="2026-07-01T00:00:00Z",
    end_date="2026-07-02T00:00:00Z",
)
```

Every list method that maps to a filterable REST endpoint accepts `filter=` for custom OData:

```python
jobs = nb.list_jobs(filter="status eq 0 and jobType eq 'BACKUP'", limit=500)
images = nb.iter_images(filter="scheduleType eq 'FULL'", client="app01")
policies = nb.list_policies(filter="active eq true")
```

Custom filters are combined with shortcut arguments using `and`.

## Services

```python
nb.list_jobs(status=0, policy="linux-prod", ignore_child_jobs=True)
nb.get_job_progress_logs(1234, limit=100)
nb.list_policies()
nb.list_policies(include_details=True)
nb.list_clients()          # hosts known by /config/hosts
nb.list_policy_clients()   # protected clients from policy details
nb.list_images(client="app01", start_date="2026-07-01T00:00:00Z", end_date="2026-07-02T00:00:00Z")
nb.get_image("app01_1234567890")
nb.list_image_contents(filter="backupId eq 'app01_1234567890'", limit=100)
nb.list_storage()
nb.list_slps()
nb.list_vm_assets()
nb.health_report()
```

The service objects are still available when you need more specific calls:

```python
nb.jobs.get(1234)
nb.policies.clients()
nb.storage.storage_units()
nb.storage.disk_pools()
nb.slp.get("gold-copy")
```

## Collectors

Collectors return `CollectionResult`, which can be converted into index-friendly dictionaries.

```python
result = nb.collect("jobs", start_date="2026-07-01T00:00:00Z", end_date="2026-07-02T00:00:00Z")
documents = result.to_indexable()
```

Collectors also accept `limit` for services that support it:

```python
result = nb.collect("images", client="app01", limit=1000)
```

The older fluent collector style is also supported:

```python
result = nb.collectors.jobs().collect(
    start_date="2026-07-01T00:00:00Z",
    end_date="2026-07-02T00:00:00Z",
)
```

The output is designed to be easy to send later to Elasticsearch, PostgreSQL, files, dashboards,
or reporting pipelines.

## Models

All normalized objects use Pydantic v2:

- `Job`
- `Policy`
- `Schedule`
- `Client`
- `Image`
- `StorageUnit`
- `DiskPool`
- `SLP`
- `VMAsset`
- `HealthCheck`
- `HealthReport`

Each model preserves the original source payload in `raw` and marks its collection source in
`source`.

## Version Handling

```python
nb.version.current
nb.version.supports("slp")
nb.version.supports("vmware_assets")
```

Unsupported features raise `FeatureNotSupportedError` with the required minimum version.

## Design Notes

NetBackup installations differ by version, installed options, RBAC permissions, and exposed API
surface. This package therefore keeps endpoint names centralized and service behavior conservative.
When adding a feature, check the official Veritas NetBackup API documentation for the exact target
version and update `nbu/version.py` plus the relevant service/model tests.


## Veritas DOC 

source : https://sort.veritas.com/public/documents/nbu/10.0/windowsandunix/productguides/html/catalog/catalog.yaml

/catalog/images
/catalog/image-contents 
/catalog/images/{backupId}
/catalog/images/contents/{requestId}


source : https://sort.veritas.com/public/documents/nbu/10.0/windowsandunix/productguides/html/config/config.yaml

/config/policies/
/config/policies/{policyName}
/config/policies/{policyName}/copy
/config/unique-policy-clients

source : https://sort.veritas.com/public/documents/nbu/10.0/windowsandunix/productguides/html/admin/admin.yaml

/admin/jobs
/admin/jobs/{jobId}
/admin/jobs/{jobId}/progress-logs
