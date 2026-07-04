from __future__ import annotations

from nbu.config import CollectionMode
from nbu.models.health import HealthCheck, HealthReport, Severity
from nbu.services.base import ServiceBase


class HealthService(ServiceBase):
    def check_all(self, *, mode: CollectionMode | None = None) -> HealthReport:
        checks = [
            self.master_reachable(mode=mode),
            self.api_available(),
            self.authentication_status(),
            self.services_status(mode=mode),
            self.failed_jobs_last_24h(mode=mode),
            self.storage_status(mode=mode),
            self.slp_backlog(mode=mode),
            self.security_status(mode=mode),
        ]
        return HealthReport.from_checks(checks)

    def master_reachable(self, *, mode: CollectionMode | None = None) -> HealthCheck:
        try:
            if self._mode(mode) == "ssh":
                self.ssh.run("bpps", "-x")
            else:
                self.api.request_text(
                    "GET",
                    self.version.endpoint("ping"),
                    authenticated=False,
                    headers={"Accept": f"text/vnd.netbackup+plain;version={self.config.api_version}"},
                )
            return HealthCheck(name="master_reachability", severity=Severity.OK, message="Master is reachable")
        except Exception as exc:  # noqa: BLE001 - health checks intentionally summarize broad failures.
            return HealthCheck(
                name="master_reachability",
                severity=Severity.CRITICAL,
                message=str(exc),
                details={"error_type": type(exc).__name__},
            )

    def api_available(self) -> HealthCheck:
        try:
            self.api.request_text(
                "GET",
                self.version.endpoint("ping"),
                authenticated=False,
                headers={"Accept": f"text/vnd.netbackup+plain;version={self.config.api_version}"},
            )
            return HealthCheck(name="api_availability", severity=Severity.OK, message="REST API is available")
        except Exception as exc:  # noqa: BLE001
            return HealthCheck(
                name="api_availability",
                severity=Severity.WARNING,
                message=str(exc),
                details={"error_type": type(exc).__name__},
            )

    def authentication_status(self) -> HealthCheck:
        try:
            self.api.ensure_authenticated()
            return HealthCheck(name="authentication", severity=Severity.OK, message="Authentication succeeded")
        except Exception as exc:  # noqa: BLE001
            return HealthCheck(
                name="authentication",
                severity=Severity.CRITICAL,
                message=str(exc),
                details={"error_type": type(exc).__name__},
            )

    def services_status(self, *, mode: CollectionMode | None = None) -> HealthCheck:
        if self._mode(mode) != "ssh":
            return HealthCheck(name="services", severity=Severity.UNKNOWN, message="Use SSH mode for bpps status")
        try:
            output = self.ssh.run("bpps", "-x")
            severity = Severity.OK if output.strip() else Severity.UNKNOWN
            return HealthCheck(name="services", severity=severity, message="NetBackup service status collected")
        except Exception as exc:  # noqa: BLE001
            return HealthCheck(name="services", severity=Severity.CRITICAL, message=str(exc))

    def failed_jobs_last_24h(self, *, mode: CollectionMode | None = None) -> HealthCheck:
        jobs = self._jobs(mode=mode)
        failed = [job for job in jobs if str(job.status) not in {"0", "None"}]
        severity = Severity.OK if not failed else Severity.WARNING
        return HealthCheck(
            name="failed_jobs_24h",
            severity=severity,
            message=f"{len(failed)} failed or non-zero jobs found",
            details={"count": len(failed)},
        )

    def storage_status(self, *, mode: CollectionMode | None = None) -> HealthCheck:
        try:
            units = self.client.storage.storage_units(mode=mode)  # type: ignore[attr-defined]
            bad = [unit.name for unit in units if unit.status and unit.status.lower() not in {"ok", "up"}]
            return HealthCheck(
                name="storage",
                severity=Severity.OK if not bad else Severity.WARNING,
                message=f"{len(bad)} storage units need attention",
                details={"storage_units": bad},
            )
        except Exception as exc:  # noqa: BLE001
            return HealthCheck(name="storage", severity=Severity.UNKNOWN, message=str(exc))

    def slp_backlog(self, *, mode: CollectionMode | None = None) -> HealthCheck:
        try:
            slps = self.client.slp.list(mode=mode)  # type: ignore[attr-defined]
            return HealthCheck(
                name="slp_backlog",
                severity=Severity.UNKNOWN,
                message="SLP definitions collected; backlog requires site-specific operation metrics",
                details={"slp_count": len(slps)},
            )
        except Exception as exc:  # noqa: BLE001
            return HealthCheck(name="slp_backlog", severity=Severity.UNKNOWN, message=str(exc))

    def security_status(self, *, mode: CollectionMode | None = None) -> HealthCheck:
        try:
            if self._mode(mode) == "ssh":
                self.ssh.run("nbcertcmd", "-listCertDetails")
            else:
                self.version.require("security")
                self.api.request("GET", self.version.endpoint("certificates"))
            return HealthCheck(name="security", severity=Severity.OK, message="Certificate status collected")
        except Exception as exc:  # noqa: BLE001
            return HealthCheck(name="security", severity=Severity.UNKNOWN, message=str(exc))

    def _jobs(self, *, mode: CollectionMode | None = None):
        try:
            return self.client.jobs.list(mode=mode)  # type: ignore[attr-defined]
        except Exception:
            return []
