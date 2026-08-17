"""Shared FastAPI dependencies: the process-wide DocumentStore, the
AuthService, and the request-scoped authenticated account.

Auth uses the opaque, server-side session token issued by
``careeros_auth.AuthService`` as the HTTP bearer token. That is a
deliberate choice over a stateless JWT: the session token is already
expiring AND revocable (logout / password change kill it immediately),
so it is strictly safer than an unrevocable JWT and reuses tested code.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException, status

from careeros_auth import AuthService
from careeros_auth.models import AuthenticatedAccount
from careeros_common import open_store
from careeros_tenancy import Permission, TenantScopedDocumentStore, has_permission


@lru_cache(maxsize=1)
def get_store() -> Any:
    # Postgres when CAREEROS_DATABASE_URL is set, else SQLite — see
    # careeros_common.open_store. Cached so one pool/connection is reused.
    return open_store()


def get_auth_service() -> AuthService:
    return AuthService(get_store())


def admin_emails() -> frozenset[str]:
    raw = os.environ.get("CAREEROS_ADMIN_EMAILS", "")
    return frozenset(email.strip().lower() for email in raw.split(",") if email.strip())


class RequestContext:
    """What every authenticated request resolves to: the account and a
    DocumentStore already scoped to its workspace (tenant)."""

    def __init__(self, account: AuthenticatedAccount, raw_store: Any) -> None:
        self.account = account
        self.raw_store = raw_store
        self.store = TenantScopedDocumentStore(raw_store, account.workspace_id)

    @property
    def is_admin(self) -> bool:
        return self.account.user.email in admin_emails()

    def require_permission(self, permission: Permission) -> None:
        if not has_permission(self.account.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="insufficient permissions"
            )


def current_context(
    authorization: Annotated[str | None, Header()] = None,
) -> RequestContext:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()
    account = get_auth_service().validate_session(token)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return RequestContext(account, get_store())


Context = Annotated[RequestContext, Depends(current_context)]
