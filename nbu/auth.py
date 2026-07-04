"""Authentication helpers for NetBackup REST APIs."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from pydantic import BaseModel


class TokenState(BaseModel):
    token: str | None = None
    expires_at: datetime | None = None

    @property
    def is_valid(self) -> bool:
        return bool(self.token) and (
            self.expires_at is None or self.expires_at > datetime.now(timezone.utc) + timedelta(seconds=30)
        )

    def update(self, token: str, expires_in: int | None = None) -> None:
        self.token = token
        self.expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=expires_in) if expires_in else None
        )

