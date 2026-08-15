"""careeros_credentials: encrypted secret storage, OAuth token lifecycle,
per-plugin permission checks, and audit logging. Agents request
capabilities; the platform — never the agent — owns the credential.
"""

from careeros_credentials.audit import AccessRecord, CredentialAuditLog
from careeros_credentials.encryption import SecretCipher
from careeros_credentials.exceptions import (
    AccessDeniedError,
    CredentialError,
    DecryptionError,
    SecretNotFoundError,
)
from careeros_credentials.oauth import OAuthProvider, OAuthToken
from careeros_credentials.permissions import check_access, credential_permission
from careeros_credentials.vault import CredentialVault

__all__ = [
    "AccessDeniedError",
    "AccessRecord",
    "CredentialAuditLog",
    "CredentialError",
    "CredentialVault",
    "DecryptionError",
    "OAuthProvider",
    "OAuthToken",
    "SecretCipher",
    "SecretNotFoundError",
    "check_access",
    "credential_permission",
]
