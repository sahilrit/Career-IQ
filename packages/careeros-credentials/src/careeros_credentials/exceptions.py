"""careeros_credentials exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class CredentialError(CareerOSError):
    """Base class for all credential/secret management errors."""


class DecryptionError(CredentialError):
    """Raised when a stored secret cannot be decrypted."""


class SecretNotFoundError(CredentialError):
    """Raised when a requested secret does not exist."""


class AccessDeniedError(CredentialError):
    """Raised when a requester lacks the permission to access a secret."""
