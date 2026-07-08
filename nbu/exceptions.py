"""Public exception hierarchy for nbu."""


class NetBackupError(Exception):
    """Base class for all library errors."""


class AuthenticationError(NetBackupError):
    """Authentication failed or no valid token is available."""


class AuthorizationError(NetBackupError):
    """The authenticated principal is not authorized."""


class UnsupportedVersionError(NetBackupError):
    """The detected or configured NetBackup version is unsupported."""


class FeatureNotSupportedError(NetBackupError):
    """A feature is unavailable for the configured NetBackup version."""


class ApiError(NetBackupError):
    """REST API request failed."""


class ParsingError(NetBackupError):
    """Command or API response parsing failed."""


class TimeoutError(NetBackupError):
    """A NetBackup operation timed out."""


class NotFoundError(NetBackupError):
    """The requested NetBackup resource was not found."""
