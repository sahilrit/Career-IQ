"""Gateway failure modes.

Every one of these is raised, never swallowed. A caller that wants a
degraded-but-working path catches ``NoProviderAvailableError`` explicitly and
falls back to its own deterministic template — it is never handed a fabricated
"AI" response.
"""

from __future__ import annotations


class LLMGatewayError(Exception):
    """Base for gateway failures."""


class NoProviderAvailableError(LLMGatewayError):
    """No configured provider could serve the call.

    Carries the per-provider reasons so the message tells the user what to fix
    (``run `claude /login```, ``set CAREEROS_AI_API_KEY``) rather than just
    reporting that AI is off.
    """

    def __init__(self, task: str, reasons: list[str]) -> None:
        self.task = task
        self.reasons = reasons
        detail = "; ".join(reasons) if reasons else "no providers configured"
        super().__init__(f"no LLM provider could serve task {task!r}: {detail}")


class ProviderCallError(LLMGatewayError):
    """A specific provider failed this call. The gateway catches this to try
    the next provider in the chain; it escapes only if every provider fails."""

    def __init__(self, provider_id: str, message: str) -> None:
        self.provider_id = provider_id
        super().__init__(f"{provider_id}: {message}")
