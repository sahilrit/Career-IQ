"""build_client: pick the right AI client from the key's shape, so users can
bring an Anthropic, Gemini, OpenRouter, OpenAI, or NVIDIA key and everything
just works.

- sk-ant-…  → Anthropic Messages API
- sk-or-…   → OpenRouter (OpenAI-compatible)
- nvapi-…   → NVIDIA NIM (OpenAI-compatible; reliable free tier)
- AIza…     → Google Gemini via its OpenAI-compatible endpoint (free tier)
- gsk_…     → Groq (OpenAI-compatible; fast, generous free tier)
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
# Google's OpenAI-compatible surface for the Gemini API: same chat/completions
# shape and Bearer auth, so the OpenAICompatibleClient talks to it unchanged.
_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/openai"
# Groq's OpenAI-compatible endpoint — very fast, generous free tier.
_GROQ_BASE = "https://api.groq.com/openai/v1"

DEFAULT_ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_OPENROUTER_MODEL = "openai/gpt-4o-mini"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_NVIDIA_MODEL = "meta/llama-3.3-70b-instruct"
# A fast model on Gemini's free tier — no billing required on the AI Studio key.
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"
# A strong model on Groq's free tier.
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"

_OPENAI_COMPATIBLE_BASE = {
    "openrouter": _OPENROUTER_BASE,
    "nvidia": _NVIDIA_BASE,
    "gemini": _GEMINI_BASE,
    "groq": _GROQ_BASE,
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
    if key.startswith("AIza"):
        return "gemini"
    if key.startswith("gsk_"):
        return "groq"
    return "openai"


def default_model_for_key(api_key: str) -> str:
    return {
        "anthropic": DEFAULT_ANTHROPIC_MODEL,
        "openrouter": DEFAULT_OPENROUTER_MODEL,
        "nvidia": DEFAULT_NVIDIA_MODEL,
        "gemini": DEFAULT_GEMINI_MODEL,
        "groq": DEFAULT_GROQ_MODEL,
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
