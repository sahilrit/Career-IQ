"""Shared encrypted-secret plumbing: one derivation of the cipher key and one
vault factory, reused by every feature that stores a workspace secret (AI
keys, Google tokens). Keeping it in one place means the encryption key is
derived identically everywhere."""

from __future__ import annotations

import base64
import hashlib
import logging
import os
from typing import Any

from careeros_credentials import (
    CredentialAuditLog,
    CredentialVault,
    SecretCipher,
    credential_permission,
)

_logger = logging.getLogger("careeros.vault")
_REQUESTER = "careeros-app"


_STRICT_ENVS = {"production", "prod", "staging"}


def cipher() -> SecretCipher:
    # Derive a valid Fernet key from CAREEROS_SECRET_KEY (Render's generated
    # random value works). Without the env var the at-rest key falls back to a
    # source-derivable constant — so every stored AI key / OAuth token could be
    # decrypted by anyone with the repo. We HARD-FAIL when CAREEROS_ENV declares
    # production/staging, and otherwise loudly warn and use the weak fallback
    # (so an existing deploy keeps working while the operator sets the key).
    raw = os.environ.get("CAREEROS_SECRET_KEY")
    if not raw:
        if os.environ.get("CAREEROS_ENV", "").lower() in _STRICT_ENVS:
            raise RuntimeError(
                "CAREEROS_SECRET_KEY must be set in production — stored secrets are "
                "encrypted with it and the fallback key is public in the repo."
            )
        _logger.warning(
            "CAREEROS_SECRET_KEY is not set; encrypting secrets with an INSECURE "
            "repo-derivable key. Set CAREEROS_SECRET_KEY (and CAREEROS_ENV=production) "
            "before storing real API keys."
        )
        raw = "careeros-dev-secret"
    key = base64.urlsafe_b64encode(hashlib.sha256(raw.encode("utf-8")).digest()).decode()
    return SecretCipher(key)


def open_vault(store: Any, service: str) -> CredentialVault:
    """A vault authorizing the first-party app for exactly this service."""

    def lookup(_requester: str) -> frozenset[str]:
        return frozenset({credential_permission(service)})

    return CredentialVault(store, cipher(), CredentialAuditLog(store), lookup_permissions=lookup)
