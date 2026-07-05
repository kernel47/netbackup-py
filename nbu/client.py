"""Top-level NetBackup client."""

from __future__ import annotations

from typing import Any

from nbu.collectors import Collectors
from nbu.config import NetBackupConfig
from nbu.services import (
    ClientsService,
    HealthService,
    ImagesService,
    JobsService,
    LicensingService,
    PoliciesService,
    SecurityService,
    SLPService,
    StorageService,
    VMService,
)
from nbu.transport.api import ApiTransport
from nbu.version import VersionManager


class NetBackup:
    """Facade for NetBackup REST API collection.

    Example:
        nb = NetBackup(
            master="master.company.com",
            username="user",
            password="secret",
            domain_type="unixpwd",
            domain_name="master.company.com",
            version="10.3",
        )
        jobs = nb.jobs.list()
    """

    def __init__(self, config: NetBackupConfig | None = None, **kwargs: Any) -> None:
        self.config = config or NetBackupConfig(**kwargs)
        self.version = VersionManager(self.config.version)
        self.api = ApiTransport(self.config)

        self.jobs = JobsService(self.config, self.api, self.version)
        self.policies = PoliciesService(self.config, self.api, self.version)
        self.clients = ClientsService(self.config, self.api, self.version)
        self.images = ImagesService(self.config, self.api, self.version)
        self.catalog = self.images
        self.storage = StorageService(self.config, self.api, self.version)
        self.slp = SLPService(self.config, self.api, self.version)
        self.vm = VMService(self.config, self.api, self.version)
        self.health = HealthService(self.config, self.api, self.version)
        self.licensing = LicensingService(self.config, self.api, self.version)
        self.security = SecurityService(self.config, self.api, self.version)
        self.collectors = Collectors(self)

        for service in (
            self.jobs,
            self.policies,
            self.clients,
            self.images,
            self.storage,
            self.slp,
            self.vm,
            self.health,
            self.licensing,
            self.security,
        ):
            service.attach_client(self)

    @classmethod
    def from_env(cls, prefix: str = "NBU_") -> "NetBackup":
        return cls(config=NetBackupConfig.from_env(prefix=prefix))

    @classmethod
    def connect(cls, **kwargs: Any) -> "NetBackup":
        client = cls(**kwargs)
        client.login()
        return client

    def login(self) -> str:
        return self.api.login()

    def ping(self) -> str:
        return self.api.request_text(
            "GET",
            self.version.endpoint("ping"),
            authenticated=False,
            headers={"Accept": f"text/vnd.netbackup+plain;version={self.config.api_version}"},
        )

    def list_jobs(self, **kwargs: Any):
        return self.jobs.list(**kwargs)

    def iter_jobs(self, **kwargs: Any):
        return self.jobs.iter(**kwargs)

    def get_job(self, job_id: int | str):
        return self.jobs.get(job_id)

    def list_policies(self, **kwargs: Any):
        return self.policies.list(**kwargs)

    def get_policy(self, policy_name: str):
        return self.policies.get(policy_name)

    def list_clients(self, **kwargs: Any):
        return self.clients.list(**kwargs)

    def list_policy_clients(self, **kwargs: Any):
        return self.policies.clients(**kwargs)

    def list_protected_clients(self, **kwargs: Any):
        return self.list_policy_clients(**kwargs)

    def list_images(self, **kwargs: Any):
        return self.images.list(**kwargs)

    def iter_images(self, **kwargs: Any):
        return self.images.iter(**kwargs)

    def list_storage(self, **kwargs: Any):
        return [*self.storage.storage_units(**kwargs), *self.storage.disk_pools(**kwargs)]

    def list_slps(self, **kwargs: Any):
        return self.slp.list(**kwargs)

    def list_vm_assets(self, **kwargs: Any):
        return self.vm.assets(**kwargs)

    def health_report(self, **kwargs: Any):
        return self.health.check_all(**kwargs)

    def collect(self, name: str, **kwargs: Any):
        return self.collectors.collect(name, **kwargs)

    def discover_version(self) -> str | None:
        """Attempt to discover the master server version from the REST API."""
        data = self.api.request("GET", self.version.endpoint("version"), authenticated=False)
        nested = data.get("data") if isinstance(data.get("data"), dict) else {}
        version = data.get("version") or data.get("netbackupVersion") or nested.get("version")
        if version:
            self.version.set_current(str(version))
            self.config.version = str(version)
        return str(version) if version else None

    def close(self) -> None:
        self.api.close()

    def __enter__(self) -> "NetBackup":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
