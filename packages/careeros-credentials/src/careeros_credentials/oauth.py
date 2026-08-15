"""Generic OAuth token model + lifecycle.

No specific provider (Gmail, Calendar, ...) is wired up here — that
requires the user's own OAuth app registration when they're ready to
connect a real account (Phase 27+). This is the reusable shape every
such integration stores in the CredentialVault, and the lifecycle logic
(is it expired, does it need refreshing) that's identical across all of
them.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol

from pydantic import BaseModel, Field


class OAuthToken(BaseModel):
    access_token: str
    refresh_token: str | None = None
    expires_at: datetime | None = None
    scope: list[str] = Field(default_factory=list)

    def is_expired(self, *, as_of: datetime | None = None) -> bool:
        if self.expires_at is None:
            return False
        return (as_of or datetime.now(UTC)) >= self.expires_at

    def needs_refresh(self, *, buffer_seconds: int = 300, as_of: datetime | None = None) -> bool:
        if self.expires_at is None:
            return False
        now = as_of or datetime.now(UTC)
        return now >= (self.expires_at - timedelta(seconds=buffer_seconds))


class OAuthProvider(Protocol):
    def build_authorization_url(self, *, state: str) -> str: ...
    def exchange_code_for_token(self, code: str) -> OAuthToken: ...
    def refresh(self, token: OAuthToken) -> OAuthToken: ...
