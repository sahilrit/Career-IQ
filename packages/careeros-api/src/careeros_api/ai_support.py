"""Resolving the AI a workspace can actually use.

Two sources, in order:

1. The workspace's own API key, held in the CredentialVault. Fastest, and the
   only option a hosted deployment has.
2. The LLM gateway, which additionally covers agent CLIs (`claude`, `codex`,
   `gemini`) that are already authenticated on the machine CareerOS runs on.

The second exists because of what the first does when it is absent: every AI
feature resolved to None and quietly degraded to templates, so a user running
CareerOS locally with a Claude subscription — and no API key — got no AI at
all. That is the zero-paid-API promise failing in the one case it was written
for. When the gateway has a usable provider, those features come on.

Falling back is deliberately opt-outable (CAREEROS_LLM_CLI_ENABLED=0): a
hosted API server should not shell out to a CLI, and a slow CLI is a bad
default for a request-scoped call."""

from __future__ import annotations

import os
from typing import Any

from careeros_ai import AIClient, build_client
from careeros_api.vault_support import open_vault
from careeros_application_engine import AICoverLetterGenerator, CoverLetterGenerator
from careeros_credentials import SecretNotFoundError
from careeros_job_discovery.llm_scoring import LlmJobScorer
from careeros_llm import GatewayAIClient, LLMGateway, LLMTask

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


# --- Gateway fallback ------------------------------------------------------

#: Built once: constructing it only inspects config and PATH, never the
#: network, but there is no reason to redo that per request.
_gateway: LLMGateway | None = None


def _local_gateway() -> LLMGateway | None:
    """The gateway, if this machine offers any provider at all.

    ``is_configured`` is a presence check, not a health check — probing every
    provider here would put a multi-second CLI launch inside request handling.
    A provider that turns out to be unusable raises at call time and the
    caller's existing template fallback takes over.
    """
    global _gateway
    if _gateway is None:
        _gateway = LLMGateway.from_env()
    return _gateway if _gateway.is_configured else None


def reset_gateway_cache() -> None:
    """Drop the cached gateway (tests, and after a config change)."""
    global _gateway
    _gateway = None


def _client_for_task(store: Any, workspace_id: str, task: LLMTask) -> AIClient | None:
    """The best AI client available to this workspace for ``task``, or None.

    A workspace key wins: it is explicit, fast, and works on a hosted server.
    Otherwise fall back to whatever this machine can reach locally.
    """
    key = _get_key(store, workspace_id)
    if key:
        return build_client(key, _model_for(store, workspace_id))
    gateway = _local_gateway()
    return GatewayAIClient(gateway, task) if gateway is not None else None


def ai_source(store: Any, workspace_id: str) -> str:
    """Where this workspace's AI comes from — for the Settings page."""
    if _get_key(store, workspace_id):
        return f"your API key ({model_label(store, workspace_id)})"
    gateway = _local_gateway()
    if gateway is None:
        return "not configured"
    names = ", ".join(p.provider_id for p in gateway.providers())
    return f"a locally authenticated CLI ({names})"


# --- Generator resolution --------------------------------------------------


def resolve_cover_letter_generator(store: Any, workspace_id: str) -> CoverLetterGenerator | None:
    client = _client_for_task(store, workspace_id, LLMTask.WRITE)
    return AICoverLetterGenerator(client) if client else None


def resolve_ai_client(store: Any, workspace_id: str) -> AIClient | None:
    """The raw AI client for features that build their own prompts (e.g. the
    audit pitch kit). None only when neither a key nor a local provider
    exists."""
    return _client_for_task(store, workspace_id, LLMTask.WRITE)


def resolve_llm_job_scorer(store: Any, workspace_id: str) -> LlmJobScorer | None:
    """The second-pass job scorer.

    Scoring is high-volume and mechanical, so it is routed as an ANALYZE task
    and can be pinned to a cheaper model independently of the writing tasks.
    Without any provider, discovery falls back to the heuristic scorer, exactly
    as before.
    """
    client = _client_for_task(store, workspace_id, LLMTask.ANALYZE)
    return LlmJobScorer(client) if client else None
