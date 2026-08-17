"""AIClient: the one seam every AI feature calls. Strings in, strings out —
it knows nothing about résumés, postings, or the domain."""

from __future__ import annotations

from typing import Protocol

DEFAULT_MODEL = "claude-haiku-4-5-20251001"


class AIError(Exception):
    """Base for all AI client failures."""


class AIAuthError(AIError):
    """The API key was rejected (401/403)."""


class AIUnavailableError(AIError):
    """Timeout, rate limit, or 5xx — transient; callers fall back."""


class AIClient(Protocol):
    def complete(self, *, system: str, prompt: str) -> str: ...
