"""build_client: pick the right AI client from the key's shape, so users can
bring an Anthropic, OpenRouter, OpenAI, or NVIDIA key and everything just works.

- sk-ant-…  → Anthropic Messages API
- sk-or-…   → OpenRouter (OpenAI-compatible)
- nvapi-…   → NVIDIA NIM (OpenAI-compatible; reliable free tier)
- anything else starting sk- → OpenAI (OpenAI-compatible)
"""

from __future__ import annotations

import httpx

from careeros_ai.anthropic_client import AnthropicClient
from careeros_ai.client import AIClient
from careeros_ai.openai_client import OpenAICompatibleClient

_OPENROUTER_BASE = "https://openrouter.ai/api/v1"
_OPENAI_BASE = "https://api.openai.com/v1"
_NVIDIA_BASE = "https://integrate.api.nvidia.com/v1"

DEFAULT_ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_OPENROUTER_MODEL = "openai/gpt-4o-mini"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_NVIDIA_MODEL = "meta/llama-3.3-70b-instruct"

_OPENAI_COMPATIBLE_BASE = {
    "openrouter": _OPENROUTER_BASE,
    "nvidia": _NVIDIA_BASE,
    "openai": _OPENAI_BASE,
}


def provider_for_key(api_key: str) -> str:
    key = api_key.strip()
    if key.startswith("sk-ant-"):
        return "anthropic"
    if key.startswith("sk-or-"):
        return "openrouter"
    if key.startswith("nvapi-"):
        return "nvidia"
    return "openai"


def default_model_for_key(api_key: str) -> str:
    return {
        "anthropic": DEFAULT_ANTHROPIC_MODEL,
        "openrouter": DEFAULT_OPENROUTER_MODEL,
        "nvidia": DEFAULT_NVIDIA_MODEL,
        "openai": DEFAULT_OPENAI_MODEL,
    }[provider_for_key(api_key)]


def build_client(
    api_key: str, model: str | None = None, *, http_client: httpx.Client | None = None
) -> AIClient:
    key = api_key.strip()
    provider = provider_for_key(key)
    chosen_model = model or default_model_for_key(key)
    if provider == "anthropic":
        return AnthropicClient(key, chosen_model, http_client=http_client)
    base = _OPENAI_COMPATIBLE_BASE[provider]
    return OpenAICompatibleClient(key, chosen_model, base, http_client=http_client)
