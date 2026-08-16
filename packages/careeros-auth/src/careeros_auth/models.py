"""Auth records: the credential attached to a tenancy User, and the
server-side session a login creates.

Only a hash of the session token is ever persisted — the raw token
lives in the client and a stolen database cannot mint valid sessions
from it.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from careeros_tenancy import Role, User


class Credential(BaseModel):
    user_id: str
    email: str
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    failed_attempts: int = 0
    locked_until: datetime | None = None


class Session(BaseModel):
    token_hash: str
    user_id: str
    workspace_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime


class PasswordResetToken(BaseModel):
    """A short-lived, single-use password-reset grant. Only the SHA-256
    hash of the raw token is stored, same as sessions."""

    token_hash: str
    user_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime
    used: bool = False


class AuthenticatedAccount(BaseModel):
    """What a validated session resolves to: the user plus the workspace
    (tenant) and role every request should be scoped by."""

    user: User
    workspace_id: str
    role: Role
