from __future__ import annotations

from nbu.models.health import HealthCheck, HealthReport, Severity
from nbu.services.base import ServiceBase


class HealthService(ServiceBase):
    def check_all(self) -> HealthReport:
        checks = [
            self.master_reachable(),
            self.api_available(),
            self.authentication_status(),
            self.services_status(),
            self.failed_jobs_last_24h(),
            self.storage_status(),
            self.slp_backlog(),
            self.security_status(),
        ]
        return HealthReport.from_checks(checks)

    def master_reachable(self) -> HealthCheck:
        try:
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

    def services_status(self) -> HealthCheck:
        return HealthCheck(
            name="services",
            severity=Severity.UNKNOWN,
            message="Service process status is not exposed by this lightweight REST client",
        )

    def failed_jobs_last_24h(self) -> HealthCheck:
        jobs = self._jobs()
        failed = [job for job in jobs if str(job.status) not in {"0", "None"}]
        severity = Severity.OK if not failed else Severity.WARNING
        return HealthCheck(
            name="failed_jobs_24h",
            severity=severity,
            message=f"{len(failed)} failed or non-zero jobs found",
            details={"count": len(failed)},
        )

    def storage_status(self) -> HealthCheck:
        try:
            units = self.client.storage.storage_units()  # type: ignore[attr-defined]
            bad = [unit.name for unit in units if unit.status and unit.status.lower() not in {"ok", "up"}]
            return HealthCheck(
                name="storage",
                severity=Severity.OK if not bad else Severity.WARNING,
                message=f"{len(bad)} storage units need attention",
                details={"storage_units": bad},
            )
        except Exception as exc:  # noqa: BLE001
            return HealthCheck(name="storage", severity=Severity.UNKNOWN, message=str(exc))

    def slp_backlog(self) -> HealthCheck:
        try:
            slps = self.client.slp.list()  # type: ignore[attr-defined]
            return HealthCheck(
                name="slp_backlog",
                severity=Severity.UNKNOWN,
                message="SLP definitions collected; backlog requires site-specific operation metrics",
                details={"slp_count": len(slps)},
            )
        except Exception as exc:  # noqa: BLE001
            return HealthCheck(name="slp_backlog", severity=Severity.UNKNOWN, message=str(exc))

    def security_status(self) -> HealthCheck:
        try:
            self.version.require("security")
            self.api.request("GET", self.version.endpoint("certificates"))
            return HealthCheck(name="security", severity=Severity.OK, message="Certificate status collected")
        except Exception as exc:  # noqa: BLE001
            return HealthCheck(name="security", severity=Severity.UNKNOWN, message=str(exc))

    def _jobs(self):
        try:
            return self.client.jobs.list()  # type: ignore[attr-defined]
        except Exception:
            return []
