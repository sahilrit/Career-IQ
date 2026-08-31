"""Centralized LLM configuration.

One place decides which providers exist, in what order they are tried, and
which task goes to which. Everything is overridable by environment variable so
a deployment can change routing without a code change.

    CAREEROS_AI_API_KEY       a single API key (vendor inferred from its shape)
    CAREEROS_LLM_PRIORITY     comma-separated provider ids, best first
    CAREEROS_LLM_CLI_ENABLED  "0" to ignore locally installed agent CLIs
    CAREEROS_LLM_TASK_<TASK>  pin one task to one provider id, e.g.
                              CAREEROS_LLM_TASK_REVIEW=gemini
"""

from __future__ import annotations

import os

from pydantic import BaseModel, Field

from careeros_llm.models import LLMTask

#: Default preference order when nothing is pinned. API keys first (fast,
#: cheap per call), then agent CLIs (free with an existing subscription but
#: slow to start). A user with neither gets a clear error, never a fake answer.
DEFAULT_PRIORITY: tuple[str, ...] = (
    "anthropic",
    "openai",
    "gemini",
    "groq",
    "openrouter",
    "nvidia",
    "claude-cli",
    "gemini-cli",
    "codex-cli",
)


def _env_flag(name: str, default: bool = True) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() not in ("0", "false", "no", "off")


class LLMConfig(BaseModel):
    """Resolved configuration for a gateway instance."""

    api_key: str = ""
    api_model: str | None = None
    #: Provider ids best-first. Unknown/absent ids are skipped silently — a
    #: priority list is a preference, not an assertion that all of them exist.
    priority: list[str] = Field(default_factory=lambda: list(DEFAULT_PRIORITY))
    cli_enabled: bool = True
    #: task -> provider id. A pinned provider is tried first for that task and
    #: the rest of the chain still applies behind it, so pinning never turns a
    #: transient outage into a hard failure.
    task_routing: dict[LLMTask, str] = Field(default_factory=dict)
    cli_timeout_seconds: float = 180.0

    @classmethod
    def from_env(cls, **overrides) -> LLMConfig:
        priority_raw = os.environ.get("CAREEROS_LLM_PRIORITY", "")
        priority = [p.strip() for p in priority_raw.split(",") if p.strip()] or list(
            DEFAULT_PRIORITY
        )
        routing: dict[LLMTask, str] = {}
        for task in LLMTask:
            pinned = os.environ.get(f"CAREEROS_LLM_TASK_{task.value.upper()}", "").strip()
            if pinned:
                routing[task] = pinned
        data = {
            "api_key": os.environ.get("CAREEROS_AI_API_KEY", "").strip(),
            "api_model": os.environ.get("CAREEROS_AI_MODEL", "").strip() or None,
            "priority": priority,
            "cli_enabled": _env_flag("CAREEROS_LLM_CLI_ENABLED"),
            "task_routing": routing,
        }
        data.update(overrides)
        return cls(**data)
