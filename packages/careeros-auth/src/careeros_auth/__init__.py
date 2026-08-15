"""careeros-auth: accounts, sessions, and passwords for the hosted SaaS."""

from careeros_auth.exceptions import (
    AccountLockedError,
    AuthError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    PasswordPolicyError,
)
from careeros_auth.models import AuthenticatedAccount, Credential, Session
from careeros_auth.password import hash_password, verify_password
from careeros_auth.service import AuthService

__all__ = [
    "AccountLockedError",
    "AuthError",
    "AuthService",
    "AuthenticatedAccount",
    "Credential",
    "EmailAlreadyRegisteredError",
    "InvalidCredentialsError",
    "PasswordPolicyError",
    "Session",
    "hash_password",
    "verify_password",
]
