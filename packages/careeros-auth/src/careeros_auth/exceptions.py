"""Auth-specific errors, all under the shared CareerOSError root so
callers can catch platform errors uniformly.
"""

from __future__ import annotations

from careeros_common.exceptions import CareerOSError


class AuthError(CareerOSError):
    """Base class for authentication failures."""


class EmailAlreadyRegisteredError(AuthError):
    """Raised on signup when the email already has an account."""


class InvalidCredentialsError(AuthError):
    """Raised on login when the email/password pair doesn't match.

    Deliberately identical for "unknown email" and "wrong password" so
    responses don't leak which emails have accounts.
    """


class AccountLockedError(AuthError):
    """Raised when login is attempted while the account is locked out
    after repeated failures."""


class PasswordPolicyError(AuthError):
    """Raised when a new password fails the security policy."""

    def __init__(self, violations: list[str]) -> None:
        self.violations = violations
        super().__init__("; ".join(violations))
