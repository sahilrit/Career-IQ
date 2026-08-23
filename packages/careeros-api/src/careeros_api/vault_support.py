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


_DEV_ENVS = {"dev", "test", "local", "ci"}


def cipher() -> SecretCipher:
    # Derive a valid Fernet key from CAREEROS_SECRET_KEY (Render's generated
    # random value works). FAIL CLOSED outside dev: without the env var the
    # at-rest key would fall back to a source-derivable constant, so every
    # stored AI key / OAuth token could be decrypted by anyone with the repo.
    raw = os.environ.get("CAREEROS_SECRET_KEY")
    if not raw:
        if os.environ.get("CAREEROS_ENV", "").lower() in _DEV_ENVS:
            raw = "careeros-dev-secret"
        else:
            raise RuntimeError(
                "CAREEROS_SECRET_KEY must be set (secrets are encrypted with it). "
                "Set CAREEROS_ENV=dev to allow the insecure dev fallback locally."
            )
    key = base64.urlsafe_b64encode(hashlib.sha256(raw.encode("utf-8")).digest()).decode()
    return SecretCipher(key)


def open_vault(store: Any, service: str) -> CredentialVault:
    """A vault authorizing the first-party app for exactly this service."""

    def lookup(_requester: str) -> frozenset[str]:
        return frozenset({credential_permission(service)})

    return CredentialVault(store, cipher(), CredentialAuditLog(store), lookup_permissions=lookup)
