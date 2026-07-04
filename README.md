# netbackup-py

`netbackup-py` provides a modern typed Python wrapper for Veritas NetBackup automation,
collection, health checks, and reporting. It is intentionally NetBackup-oriented and exposes
the import package as `nbu`.

The library targets NetBackup 9.x, 10.x, and newer. REST endpoint mappings are centralized in
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

**Important:** the main `nbu` package requires Python 3.12+.

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

Optional SSH and development dependencies:

```bash
pip install -r requirements-ssh.txt
pip install -r requirements-dev.txt
```

Because this is a package, `pyproject.toml` is the main dependency definition. The
`requirements*.txt` files are provided for simple deployments and scripts.

### Python 3.6 legacy usage

Python 3.6 cannot install the main package dependencies (`httpx>=0.27` and Pydantic v2). If you
are forced to run on Python 3.6, use the standalone legacy example instead:

```bash
python3.6 -m pip install -r requirements-py36.txt
python3.6 examples/legacy_py36_basic.py
```

The legacy script uses only `requests` and supports basic REST login, paginated jobs, and
paginated images. It does not provide typed Pydantic models or the full `nbu` package API.

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

    jobs = nb.list_jobs(start_date="2026-07-01", end_date="2026-07-02", limit=100)
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
images = nb.list_images(client="app01", start_date="2026-07-01", end_date="2026-07-02")
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

## Collection Modes

Every major service accepts `mode="api"` or `mode="ssh"`.

API mode uses the NetBackup REST API with token login, NetBackup vendor media headers,
domain-aware authentication, pagination, retries, timeouts, SSL verification configuration,
and optional proxy settings.

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

## Large Collections

By default, list methods collect every page that NetBackup returns:

```python
jobs = nb.list_jobs(start_date="2026-07-01", end_date="2026-07-02")
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
for job in nb.iter_jobs(start_date="2026-07-01", end_date="2026-07-02"):
    process(job)

for image in nb.iter_images(client="app01", limit=10_000):
    process(image)
```

Streaming still follows NetBackup pagination, but it yields records one by one instead of building
one large list first. The safest production pattern is to combine streaming with date filters.

SSH mode executes safe read-only NetBackup commands such as `bpdbjobs`, `bppllist`,
`bpimagelist`, `bpstulist`, `nbemmcmd`, `nbstl`, `nbdeployutil`, `nbcertcmd`, `vmquery`, and
`nbdiscover`, then normalizes output into the same Pydantic models used by API mode.

## Services

```python
nb.list_jobs(status=0, policy="linux-prod", ignore_child_jobs=True)
nb.list_policies()
nb.list_clients()
nb.list_images(client="app01", start_date="2026-07-01", end_date="2026-07-02")
nb.list_storage()
nb.list_slps()
nb.list_vm_assets()
nb.health_report()
```

The service objects are still available when you need more specific calls:

```python
nb.jobs.get(1234)
nb.storage.storage_units()
nb.storage.disk_pools()
nb.slp.get("gold-copy")
```

## Collectors

Collectors return `CollectionResult`, which can be converted into index-friendly dictionaries.

```python
result = nb.collect("jobs", start_date="2026-07-01", end_date="2026-07-02", mode="api")
documents = result.to_indexable()
```

Collectors also accept `limit` for services that support it:

```python
result = nb.collect("images", client="app01", limit=1000)
```

The older fluent collector style is also supported:

```python
result = nb.collectors.jobs().collect(start_date="2026-07-01", end_date="2026-07-02")
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
surface. This package therefore keeps endpoint names centralized and parser behavior conservative.
When adding a feature, check the official Veritas NetBackup API documentation for the exact target
version and update `nbu/version.py` plus the relevant service/model tests.
