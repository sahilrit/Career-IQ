"""AIClient: the one seam every AI feature calls. Strings in, strings out —
it knows nothing about résumés, postings, or the domain."""

from __future__ import annotations

import os
from typing import Protocol

DEFAULT_MODEL = "claude-haiku-4-5-20251001"


def default_timeout() -> float:
    """Read timeout for AI calls. Generous by default so slow free tiers
    (e.g. NVIDIA's free NIM) have room to respond; override with
    CAREEROS_AI_TIMEOUT (seconds)."""
    try:
        return float(os.environ.get("CAREEROS_AI_TIMEOUT", "120"))
    except ValueError:
        return 120.0


class AIError(Exception):
    """Base for all AI client failures."""


class AIAuthError(AIError):
    """The API key was rejected (401/403)."""


class AIUnavailableError(AIError):
    """Timeout, rate limit, or 5xx — transient; callers fall back."""


class AIClient(Protocol):
    def complete(self, *, system: str, prompt: str) -> str: ...
