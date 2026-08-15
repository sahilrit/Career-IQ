"""AuthService: the one place signup, login, sessions, and password
changes happen.

Signup provisions the complete tenancy chain in one call — User,
Organization, Workspace, owner Membership, and a Free-tier
Subscription — so a brand-new account lands fully formed and every
other package's tenant-scoping works immediately.

The clock is injectable (``now=``) so lockout and session expiry are
testable without sleeping.
"""

from __future__ import annotations

import hashlib
import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from careeros_auth.exceptions import (
    AccountLockedError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    PasswordPolicyError,
)
from careeros_auth.models import AuthenticatedAccount, Credential, Session
from careeros_auth.password import hash_password, verify_password
from careeros_billing import Subscription, SubscriptionRepository
from careeros_billing.plan import PlanTier
from careeros_common import DocumentStore
from careeros_compliance.security_policy import SecurityPolicy, check_password
from careeros_tenancy import Membership, Organization, Role, TenancyRepository, User, Workspace

_CREDENTIAL_TYPE = "auth_credential"
_SESSION_TYPE = "auth_session"

_MAX_FAILED_ATTEMPTS = 5
_LOCKOUT = timedelta(minutes=15)
_DEFAULT_SESSION_LIFETIME = timedelta(days=7)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class AuthService:
    def __init__(
        self,
        store: DocumentStore,
        *,
        policy: SecurityPolicy | None = None,
        session_lifetime: timedelta = _DEFAULT_SESSION_LIFETIME,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store
        self._tenancy = TenancyRepository(store)
        self._subscriptions = SubscriptionRepository(store)
        self._policy = policy or SecurityPolicy()
        self._session_lifetime = session_lifetime
        self._now = now or (lambda: datetime.now(UTC))

    # -- signup ---------------------------------------------------------

    def sign_up(self, *, email: str, password: str, full_name: str) -> tuple[User, str]:
        """Create the account and everything it needs; returns the user
        and a live session token (signup logs you in)."""
        normalized = email.strip().lower()
        if self._tenancy.find_user_by_email(normalized) is not None:
            raise EmailAlreadyRegisteredError(f"{normalized} already has an account")
        violations = check_password(password, self._policy)
        if violations:
            raise PasswordPolicyError(violations)

        user = User(email=normalized, full_name=full_name.strip())
        organization = Organization(name=f"{user.full_name or normalized} — personal")
        workspace = Workspace(organization_id=organization.id, name="Personal")
        self._tenancy.save_user(user)
        self._tenancy.save_organization(organization)
        self._tenancy.save_workspace(workspace)
        self._tenancy.add_membership(
            Membership(user_id=user.id, workspace_id=workspace.id, role=Role.OWNER)
        )
        self._subscriptions.save(Subscription(workspace_id=workspace.id, plan_tier=PlanTier.FREE))
        self._save_credential(
            Credential(user_id=user.id, email=normalized, password_hash=hash_password(password))
        )
        return user, self._create_session(user.id, workspace.id)

    # -- login / sessions ------------------------------------------------

    def log_in(self, *, email: str, password: str) -> str:
        normalized = email.strip().lower()
        user = self._tenancy.find_user_by_email(normalized)
        credential = self._load_credential(user.id) if user else None
        if user is None or credential is None:
            raise InvalidCredentialsError("email or password is incorrect")

        current_time = self._now()
        if credential.locked_until is not None and credential.locked_until > current_time:
            raise AccountLockedError("too many failed attempts — try again in a few minutes")

        if not verify_password(password, credential.password_hash):
            credential.failed_attempts += 1
            if credential.failed_attempts >= _MAX_FAILED_ATTEMPTS:
                credential.locked_until = current_time + _LOCKOUT
                credential.failed_attempts = 0
            self._save_credential(credential)
            raise InvalidCredentialsError("email or password is incorrect")

        credential.failed_attempts = 0
        credential.locked_until = None
        self._save_credential(credential)

        memberships = self._tenancy.workspaces_for_user(user.id)
        if not memberships:
            raise InvalidCredentialsError("account has no workspace")
        return self._create_session(user.id, memberships[0].workspace_id)

    def validate_session(self, token: str) -> AuthenticatedAccount | None:
        data = self._store.get_or_none(_SESSION_TYPE, _token_hash(token))
        if data is None:
            return None
        session = Session.model_validate(data)
        if session.expires_at <= self._now():
            self._store.delete(_SESSION_TYPE, session.token_hash)
            return None
        user = self._tenancy.load_user(session.user_id)
        membership = (
            self._tenancy.membership_for(session.user_id, session.workspace_id) if user else None
        )
        if user is None or membership is None:
            self._store.delete(_SESSION_TYPE, session.token_hash)
            return None
        return AuthenticatedAccount(
            user=user, workspace_id=session.workspace_id, role=membership.role
        )

    def log_out(self, token: str) -> None:
        if self._store.get_or_none(_SESSION_TYPE, _token_hash(token)) is not None:
            self._store.delete(_SESSION_TYPE, _token_hash(token))

    def log_out_everywhere(self, user_id: str) -> int:
        """Revoke every session for the user; returns how many were revoked."""
        revoked = 0
        for data in self._store.list(_SESSION_TYPE):
            if data.get("user_id") == user_id:
                self._store.delete(_SESSION_TYPE, data["token_hash"])
                revoked += 1
        return revoked

    # -- password management ----------------------------------------------

    def change_password(self, user_id: str, *, current_password: str, new_password: str) -> None:
        credential = self._load_credential(user_id)
        if credential is None or not verify_password(current_password, credential.password_hash):
            raise InvalidCredentialsError("current password is incorrect")
        violations = check_password(new_password, self._policy)
        if violations:
            raise PasswordPolicyError(violations)
        credential.password_hash = hash_password(new_password)
        self._save_credential(credential)
        self.log_out_everywhere(user_id)

    def delete_account(self, user_id: str) -> None:
        """Remove credential, sessions, memberships, and the user record.

        Tenant-scoped domain data is the caller's responsibility (via the
        trust layer's data-deletion registry) — this only removes identity.
        """
        self.log_out_everywhere(user_id)
        if self._load_credential(user_id) is not None:
            self._store.delete(_CREDENTIAL_TYPE, user_id)
        for membership in self._tenancy.workspaces_for_user(user_id):
            self._tenancy.remove_membership(user_id, membership.workspace_id)
        self._tenancy.delete_user(user_id)

    # -- internals ---------------------------------------------------------

    def _create_session(self, user_id: str, workspace_id: str) -> str:
        token = secrets.token_urlsafe(32)
        session = Session(
            token_hash=_token_hash(token),
            user_id=user_id,
            workspace_id=workspace_id,
            expires_at=self._now() + self._session_lifetime,
        )
        self._store.put(_SESSION_TYPE, session.token_hash, session.model_dump(mode="json"))
        return token

    def _save_credential(self, credential: Credential) -> None:
        self._store.put(_CREDENTIAL_TYPE, credential.user_id, credential.model_dump(mode="json"))

    def _load_credential(self, user_id: str) -> Credential | None:
        data = self._store.get_or_none(_CREDENTIAL_TYPE, user_id)
        return Credential.model_validate(data) if data else None
