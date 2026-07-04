"""Typed automation library for Veritas NetBackup."""

from nbu.client import NetBackup
from nbu.config import NetBackupConfig
from nbu.exceptions import (
    ApiError,
    AuthenticationError,
    AuthorizationError,
    FeatureNotSupportedError,
    NetBackupError,
    NotFoundError,
    ParsingError,
    SshError,
    TimeoutError,
    UnsupportedVersionError,
)

__all__ = [
    "ApiError",
    "AuthenticationError",
    "AuthorizationError",
    "FeatureNotSupportedError",
    "NetBackup",
    "NetBackupConfig",
    "NetBackupError",
    "NotFoundError",
    "ParsingError",
    "SshError",
    "TimeoutError",
    "UnsupportedVersionError",
]

