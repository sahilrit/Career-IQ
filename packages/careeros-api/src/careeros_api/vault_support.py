"""Shared encrypted-secret plumbing: one derivation of the cipher key and one
vault factory, reused by every feature that stores a workspace secret (AI
keys, Google tokens). Keeping it in one place means the encryption key is
derived identically everywhere."""

from __future__ import annotations

import base64
import hashlib
import os
from typing import Any

from careeros_credentials import (
    CredentialAuditLog,
    CredentialVault,
    SecretCipher,
    credential_permission,
)

_REQUESTER = "careeros-app"


def cipher() -> SecretCipher:
    # Derive a valid Fernet key from any CAREEROS_SECRET_KEY string (so
    # Render's generated random value works). Deterministic; dev fallback
    # when unset (never used in production).
    raw = os.environ.get("CAREEROS_SECRET_KEY") or "careeros-dev-secret"
    key = base64.urlsafe_b64encode(hashlib.sha256(raw.encode("utf-8")).digest()).decode()
    return SecretCipher(key)


def open_vault(store: Any, service: str) -> CredentialVault:
    """A vault authorizing the first-party app for exactly this service."""

    def lookup(_requester: str) -> frozenset[str]:
        return frozenset({credential_permission(service)})

    return CredentialVault(store, cipher(), CredentialAuditLog(store), lookup_permissions=lookup)
