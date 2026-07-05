from nbu.config import NetBackupConfig
from nbu.filters import combine, contains, expr, raw_expr


def test_api_version_is_inferred_for_official_doc_versions() -> None:
    assert NetBackupConfig(master="m", version="10.0").api_version == "7.0"
    assert NetBackupConfig(master="m", version="10.1").api_version == "8.0"
    assert NetBackupConfig(master="m", version="10.2").api_version == "9.0"
    assert NetBackupConfig(master="m", version="10.3").api_version == "10.0"
    assert NetBackupConfig(master="m", version="10.4").api_version == "11.0"
    assert NetBackupConfig(master="m", version="11.0").api_version == "13.0"
    assert NetBackupConfig(master="m", version="11.1").api_version == "14.0"
    assert NetBackupConfig(master="m", version="11.2").api_version == "14.0"
    assert NetBackupConfig(master="m").api_version == "7.0"
    assert NetBackupConfig(master="m", version="11.2").service_api_version("config_policies") == "12.0"
    assert NetBackupConfig(master="m", version="11.2").service_api_version("catalog") == "14.0"


def test_odata_filter_helpers() -> None:
    assert expr("status", "eq", 0) == "status eq 0"
    assert expr("clientName", "eq", "app01") == "clientName eq 'app01'"
    assert raw_expr("startTime", "ge", "2026-07-01T00:00:00Z") == (
        "startTime ge 2026-07-01T00:00:00Z"
    )
    assert contains("policyName", "prod") == "contains(policyName,'prod')"
    assert combine(expr("status", "eq", 0), expr("jobType", "eq", "BACKUP")) == (
        "status eq 0 and jobType eq 'BACKUP'"
    )
