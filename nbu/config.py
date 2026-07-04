"""Configuration models."""

from __future__ import annotations

import os
from typing import Literal

from pydantic import BaseModel, Field, SecretStr, model_validator

CollectionMode = Literal["api", "ssh"]


class NetBackupConfig(BaseModel):
    """Connection settings for a NetBackup master server."""

    master: str
    username: str | None = None
    password: SecretStr | None = None
    domain_type: str = ""
    domain_name: str = ""
    token: SecretStr | None = None
    version: str | None = None
    api_version: str | None = None
    page_limit: int = 100
    authorization_scheme: str = ""
    base_url: str | None = None
    verify_ssl: bool = True
    timeout: float = 30.0
    retries: int = 3
    retry_backoff: float = 0.5
    proxies: dict[str, str] | None = None
    mode: CollectionMode = "api"
    ssh_port: int = 22
    ssh_key_filename: str | None = None
    command_timeout: float = 120.0
    user_agent: str = "netbackup-py/0.1.0"
    extra_headers: dict[str, str] = Field(default_factory=dict)

    @classmethod
    def from_env(cls, prefix: str = "NBU_") -> "NetBackupConfig":
        """Build configuration from environment variables.

        Common variables:
        NBU_MASTER, NBU_USERNAME, NBU_PASSWORD, NBU_TOKEN, NBU_DOMAIN_TYPE,
        NBU_DOMAIN_NAME, NBU_VERSION, NBU_API_VERSION, NBU_VERIFY_SSL.
        """

        def env(name: str) -> str | None:
            return os.getenv(f"{prefix}{name}")

        master = env("MASTER")
        if not master:
            raise ValueError(f"{prefix}MASTER is required")

        verify_ssl = env("VERIFY_SSL")
        return cls(
            master=master,
            username=env("USERNAME"),
            password=env("PASSWORD"),
            token=env("TOKEN"),
            domain_type=env("DOMAIN_TYPE") or "",
            domain_name=env("DOMAIN_NAME") or "",
            version=env("VERSION"),
            api_version=env("API_VERSION"),
            base_url=env("BASE_URL"),
            verify_ssl=False if verify_ssl and verify_ssl.lower() in {"0", "false", "no"} else True,
        )

    @model_validator(mode="after")
    def infer_api_version(self) -> "NetBackupConfig":
        if self.api_version:
            return self
        if self.version:
            major_minor = ".".join(self.version.split(".")[:2])
            self.api_version = {
                "10.0": "7.0",
                "11.2": "14.0",
            }.get(major_minor)
        self.api_version = self.api_version or "3.0"
        return self

    @property
    def api_base_url(self) -> str:
        if self.base_url:
            return self.base_url.rstrip("/")
        return f"https://{self.master}/netbackup"
