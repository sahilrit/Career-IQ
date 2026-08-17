"""First-party wrapper over CredentialVault for the workspace's AI key
(Anthropic / OpenRouter / OpenAI) and optional model, plus generator
resolution. The app is authorized explicitly (not a third-party plugin)."""

from __future__ import annotations

import os
from typing import Any

from careeros_ai import AIClient, build_client
from careeros_api.vault_support import open_vault
from careeros_application_engine import AICoverLetterGenerator, CoverLetterGenerator
from careeros_credentials import SecretNotFoundError

_KEY_SERVICE = "anthropic_api_key"  # kept for back-compat with stored keys
_MODEL_SERVICE = "ai_model"
_REQUESTER = "careeros-app"


def _vault(store: Any, service: str):
    return open_vault(store, service)


def ai_model_override() -> str | None:
    """Global model override (env) — a workspace model takes precedence."""
    return os.environ.get("CAREEROS_AI_MODEL") or None


# --- Key -------------------------------------------------------------------


def store_workspace_key(store: Any, workspace_id: str, api_key: str) -> None:
    _vault(store, _KEY_SERVICE).store_secret(
        workspace_id, _KEY_SERVICE, api_key, requester_id=_REQUESTER
    )


def delete_workspace_key(store: Any, workspace_id: str) -> None:
    _vault(store, _KEY_SERVICE).delete_secret(workspace_id, _KEY_SERVICE, requester_id=_REQUESTER)
    store_workspace_model(store, workspace_id, None)  # clear the model too


def has_workspace_key(store: Any, workspace_id: str) -> bool:
    return _vault(store, _KEY_SERVICE).has_secret(workspace_id, _KEY_SERVICE)


def _get_key(store: Any, workspace_id: str) -> str | None:
    try:
        return _vault(store, _KEY_SERVICE).get_secret(
            workspace_id, _KEY_SERVICE, requester_id=_REQUESTER
        )
    except SecretNotFoundError:
        return None


# --- Model (optional, per workspace) ---------------------------------------


def store_workspace_model(store: Any, workspace_id: str, model: str | None) -> None:
    vault = _vault(store, _MODEL_SERVICE)
    if model:
        vault.store_secret(workspace_id, _MODEL_SERVICE, model, requester_id=_REQUESTER)
    elif vault.has_secret(workspace_id, _MODEL_SERVICE):
        vault.delete_secret(workspace_id, _MODEL_SERVICE, requester_id=_REQUESTER)


def workspace_model(store: Any, workspace_id: str) -> str | None:
    try:
        return _vault(store, _MODEL_SERVICE).get_secret(
            workspace_id, _MODEL_SERVICE, requester_id=_REQUESTER
        )
    except SecretNotFoundError:
        return None


def _model_for(store: Any, workspace_id: str) -> str | None:
    """Workspace model wins, then the global env override, else provider default."""
    return workspace_model(store, workspace_id) or ai_model_override()


def model_label(store: Any, workspace_id: str) -> str:
    """Human label for the Settings page."""
    return _model_for(store, workspace_id) or "your provider's default"


# --- Generator resolution --------------------------------------------------


def resolve_cover_letter_generator(store: Any, workspace_id: str) -> CoverLetterGenerator | None:
    key = _get_key(store, workspace_id)
    if not key:
        return None
    return AICoverLetterGenerator(build_client(key, _model_for(store, workspace_id)))


def resolve_ai_client(store: Any, workspace_id: str) -> AIClient | None:
    """The raw AI client for features that build their own prompts (e.g. the
    audit pitch kit). Works with Anthropic, OpenRouter, or OpenAI keys. None
    when the workspace has no key."""
    key = _get_key(store, workspace_id)
    if not key:
        return None
    return build_client(key, _model_for(store, workspace_id))
