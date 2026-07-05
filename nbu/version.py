"""NetBackup version management and endpoint resolution."""

from __future__ import annotations

from dataclasses import dataclass
from functools import total_ordering

from nbu.exceptions import FeatureNotSupportedError, UnsupportedVersionError


@total_ordering
@dataclass(frozen=True)
class NetBackupVersion:
    """Comparable NetBackup semantic-ish version."""

    major: int
    minor: int = 0
    patch: int = 0

    @classmethod
    def parse(cls, value: str | None) -> "NetBackupVersion | None":
        if not value:
            return None
        parts = []
        for token in value.replace("-", ".").split("."):
            if token.isdigit():
                parts.append(int(token))
            elif token:
                break
        if not parts:
            raise UnsupportedVersionError(f"Cannot parse NetBackup version: {value!r}")
        return cls(*(parts + [0, 0])[:3])

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, NetBackupVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


FEATURE_MIN_VERSION = {
    "jobs": "10.0",
    "policies": "10.0",
    "clients": "10.0",
    "images": "10.0",
    "catalog": "10.0",
    "storage": "10.0",
    "slp": "10.0",
    "vmware_preview": "10.0",
    "health": "10.0",
    "licensing": "10.0",
    "security": "10.0",
}


ENDPOINTS = {
    "login": "/login",
    "version": "/appdetails",
    "ping": "/ping",
    "jobs": "/admin/jobs",
    "job": "/admin/jobs/{job_id}",
    "policies": "/config/policies/",
    "policy": "/config/policies/{policy_name}",
    "unique_policy_clients": "/config/unique-policy-clients",
    "clients": "/config/hosts",
    "client": "/config/hosts/{client_name}",
    "images": "/catalog/images",
    "image": "/catalog/images/{backup_id}",
    "image_contents": "/catalog/image-contents",
    "image_contents_request": "/catalog/images/contents/{request_id}",
    "storage_units": "/storage/storage-units",
    "disk_pools": "/storage/disk-pools",
    "slp": "/config/slps",
    "slp_detail": "/config/slps/{slp_name}",
    "preview_asset_group": "/config/preview-asset-group",
    "health": "/admin/health",
    "licenses": "/admin/licenses",
    "certificates": "/security/certificates",
    "job_progress_logs": "/admin/jobs/{job_id}/progress-logs",
    "policy_copy": "/config/policies/{policy_name}/copy",
}


class VersionManager:
    """Detects version capabilities and resolves documented API paths.

    NetBackup exposes version-specific OpenAPI documentation from the master
    server. This manager centralizes endpoint names so callers can override or
    extend mappings when a site-specific version differs from the defaults.
    """

    def __init__(self, version: str | None = None, endpoints: dict[str, str] | None = None) -> None:
        self.current = NetBackupVersion.parse(version)
        self._endpoints = ENDPOINTS | (endpoints or {})

    def set_current(self, version: str | None) -> None:
        self.current = NetBackupVersion.parse(version)

    def supports(self, feature: str) -> bool:
        minimum = NetBackupVersion.parse(FEATURE_MIN_VERSION.get(feature))
        if minimum is None:
            return False
        return self.current is None or self.current >= minimum

    def require(self, feature: str) -> None:
        if not self.supports(feature):
            raise FeatureNotSupportedError(
                f"Feature {feature!r} requires NetBackup {FEATURE_MIN_VERSION[feature]} or newer; "
                f"current version is {self.current}."
            )

    def endpoint(self, name: str, **path_params: object) -> str:
        try:
            template = self._endpoints[name]
        except KeyError as exc:
            raise FeatureNotSupportedError(f"No endpoint mapping exists for {name!r}.") from exc
        return template.format(**path_params)
