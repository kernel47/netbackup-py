from nbu.config import NetBackupConfig
from nbu.filters import combine, contains, expr


def test_api_version_is_inferred_for_official_doc_versions() -> None:
    assert NetBackupConfig(master="m", version="10.0").api_version == "7.0"
    assert NetBackupConfig(master="m", version="11.2").api_version == "14.0"


def test_odata_filter_helpers() -> None:
    assert expr("status", "eq", 0) == "status eq 0"
    assert expr("clientName", "eq", "app01") == "clientName eq 'app01'"
    assert contains("policyName", "prod") == "contains(policyName,'prod')"
    assert combine(expr("status", "eq", 0), expr("jobType", "eq", "BACKUP")) == (
        "status eq 0 and jobType eq 'BACKUP'"
    )
