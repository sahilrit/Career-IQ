"""First-party wrapper over CredentialVault for the workspace's Anthropic
key, plus generator resolution. The app is authorized explicitly (it is
not a third-party plugin)."""

from __future__ import annotations

import base64
import hashlib
import os
from typing import Any

from careeros_ai import AIClient, build_client
from careeros_application_engine import AICoverLetterGenerator, CoverLetterGenerator
from careeros_credentials import (
    CredentialAuditLog,
    CredentialVault,
    SecretCipher,
    SecretNotFoundError,
    credential_permission,
)

_SERVICE = "anthropic_api_key"
_REQUESTER = "careeros-app"


def _cipher() -> SecretCipher:
    # Derive a valid Fernet key from any secret string so operators can set
    # CAREEROS_SECRET_KEY to an arbitrary value (e.g. Render's generated
    # random string) without it having to already be Fernet-formatted.
    # Deterministic: the same secret always yields the same key, so stored
    # secrets keep decrypting. Falls back to a fixed dev secret when unset
    # (never used in production, which always sets the env).
    raw = os.environ.get("CAREEROS_SECRET_KEY") or "careeros-dev-secret"
    key = base64.urlsafe_b64encode(hashlib.sha256(raw.encode("utf-8")).digest()).decode()
    return SecretCipher(key)


def _vault(store: Any) -> CredentialVault:
    def lookup(_requester: str) -> frozenset[str]:
        return frozenset({credential_permission(_SERVICE)})

    return CredentialVault(store, _cipher(), CredentialAuditLog(store), lookup_permissions=lookup)


def ai_model_override() -> str | None:
    """A specific model to force across providers, or None to let each
    provider use its default."""
    return os.environ.get("CAREEROS_AI_MODEL") or None


def ai_model() -> str:
    """Human label for the Settings page."""
    return os.environ.get("CAREEROS_AI_MODEL") or "your provider's default"


def store_workspace_key(store: Any, workspace_id: str, api_key: str) -> None:
    _vault(store).store_secret(workspace_id, _SERVICE, api_key, requester_id=_REQUESTER)


def delete_workspace_key(store: Any, workspace_id: str) -> None:
    _vault(store).delete_secret(workspace_id, _SERVICE, requester_id=_REQUESTER)


def has_workspace_key(store: Any, workspace_id: str) -> bool:
    return _vault(store).has_secret(workspace_id, _SERVICE)


def _get_key(store: Any, workspace_id: str) -> str | None:
    try:
        return _vault(store).get_secret(workspace_id, _SERVICE, requester_id=_REQUESTER)
    except SecretNotFoundError:
        return None


def resolve_cover_letter_generator(store: Any, workspace_id: str) -> CoverLetterGenerator | None:
    key = _get_key(store, workspace_id)
    if not key:
        return None
    return AICoverLetterGenerator(build_client(key, ai_model_override()))


def resolve_ai_client(store: Any, workspace_id: str) -> AIClient | None:
    """The raw AI client for features that build their own prompts (e.g. the
    audit pitch kit). Works with Anthropic, OpenRouter, or OpenAI keys. None
    when the workspace has no key."""
    key = _get_key(store, workspace_id)
    if not key:
        return None
    return build_client(key, ai_model_override())
