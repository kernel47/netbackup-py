"""Top-level NetBackup client."""

from __future__ import annotations

from typing import Any

from nbu.collectors import Collectors
from nbu.config import NetBackupConfig
from nbu.services import (
    ImagesService,
    JobsService,
    PoliciesService,
    SLPService,
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
        self.images = ImagesService(self.config, self.api, self.version)
        self.catalog = self.images
        self.slp = SLPService(self.config, self.api, self.version)
        self.collectors = Collectors(self)

        for service in (
            self.jobs,
            self.policies,
            self.images,
            self.slp,
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

    def api_request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        headers: dict[str, str] | None = None,
        api_version: str | None = None,
        authenticated: bool = True,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Call any NetBackup JSON endpoint with raw params/body."""
        request_kwargs: dict[str, Any] = {}
        if params is not None:
            request_kwargs["params"] = params
        if json is not None:
            request_kwargs["json"] = json
        if data is not None:
            request_kwargs["data"] = data
        request_kwargs.update(kwargs)
        return self.api.call(
            method,
            path,
            authenticated=authenticated,
            api_version=api_version,
            headers=headers,
            **request_kwargs,
        )

    def api_get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        api_version: str | None = None,
        authenticated: bool = True,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.api_request(
            "GET",
            path,
            params=params,
            headers=headers,
            api_version=api_version,
            authenticated=authenticated,
            **kwargs,
        )

    def api_post(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        headers: dict[str, str] | None = None,
        api_version: str | None = None,
        authenticated: bool = True,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.api_request(
            "POST",
            path,
            params=params,
            json=json,
            data=data,
            headers=headers,
            api_version=api_version,
            authenticated=authenticated,
            **kwargs,
        )

    def list_jobs(self, **kwargs: Any):
        return self.jobs.list(**kwargs)

    def iter_jobs(self, **kwargs: Any):
        return self.jobs.iter(**kwargs)

    def list_recent_jobs(self, hours: int | float = 24, **kwargs: Any):
        return self.jobs.list(last_hours=hours, **kwargs)

    def list_jobs_last_24h(self, **kwargs: Any):
        return self.list_recent_jobs(24, **kwargs)

    def list_jobs_last_hour(self, **kwargs: Any):
        return self.list_recent_jobs(1, **kwargs)

    def list_running_jobs(self, **kwargs: Any):
        return self.jobs.list(job_state="running", **kwargs)

    def list_finished_jobs(self, **kwargs: Any):
        return self.jobs.list(job_state="done", **kwargs)

    def get_job(self, job_id: int | str):
        return self.jobs.get(job_id)

    def get_job_progress_logs(self, job_id: int | str, **kwargs: Any):
        return self.jobs.progress_logs(job_id, **kwargs)

    def list_policies(self, **kwargs: Any):
        return self.policies.list(**kwargs)

    def get_policy(self, policy_name: str):
        return self.policies.get(policy_name)

    def list_policy_clients(self, **kwargs: Any):
        return self.policies.clients(**kwargs)

    def list_protected_clients(self, **kwargs: Any):
        return self.list_policy_clients(**kwargs)

    def list_images(self, **kwargs: Any):
        return self.images.list(**kwargs)

    def iter_images(self, **kwargs: Any):
        return self.images.iter(**kwargs)

    def list_recent_images(self, hours: int | float = 24, **kwargs: Any):
        return self.images.list(last_hours=hours, **kwargs)

    def list_images_last_24h(self, **kwargs: Any):
        return self.list_recent_images(24, **kwargs)

    def list_images_last_hour(self, **kwargs: Any):
        return self.list_recent_images(1, **kwargs)

    def get_image(self, backup_id: str):
        return self.images.get(backup_id)

    def list_image_contents(self, **kwargs: Any):
        return self.images.contents(**kwargs)

    def get_image_contents_result(self, request_id: str):
        return self.images.contents_result(request_id)

    def list_slps(self, **kwargs: Any):
        return self.slp.list(**kwargs)

    def get_slp(self, slp_name: str):
        return self.slp.get(slp_name)

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
