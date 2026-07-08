import pytest

from nbu.exceptions import FeatureNotSupportedError
from nbu.version import NetBackupVersion, VersionManager


def test_version_comparison() -> None:
    assert NetBackupVersion.parse("10.3") > NetBackupVersion.parse("9.1")


def test_feature_support() -> None:
    version = VersionManager("10.0")
    assert version.supports("jobs")
    assert version.supports("policies")
    assert version.supports("images")
    assert version.supports("slp")


def test_require_unsupported_feature() -> None:
    with pytest.raises(FeatureNotSupportedError):
        VersionManager("9.0").require("jobs")
