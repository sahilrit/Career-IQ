"""Gateway failure modes.

Every one of these is raised, never swallowed. A caller that wants a
degraded-but-working path catches ``NoProviderAvailableError`` explicitly and
falls back to its own deterministic template — it is never handed a fabricated
"AI" response.
"""

from __future__ import annotations

from careeros_llm.models import FailureKind, classify_failure


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
    the next provider in the chain; it escapes only if every provider fails.

    ``kind`` is what separates "try again" from "tell the user to log in".
    It is inferred from the message when a provider does not classify its own
    failure, so every existing raise site keeps working and still gets a
    usable classification.
    """

    def __init__(self, provider_id: str, message: str, kind: FailureKind | None = None) -> None:
        self.provider_id = provider_id
        self.detail = message
        self.kind = kind if kind is not None else classify_failure(message)
        super().__init__(f"{provider_id}: {message}")

    @property
    def is_retryable(self) -> bool:
        """Whether re-asking THIS provider could plausibly work. Moving to a
        different provider is always allowed and is not governed by this."""
        return self.kind.is_retryable


class MalformedResponseError(ProviderCallError):
    """The provider answered, but not in the shape the caller requires.

    Retryable by construction: asking again with a stricter instruction is the
    one failure mode where a same-provider retry reliably helps.
    """

    def __init__(self, provider_id: str, message: str) -> None:
        super().__init__(provider_id, message, kind=FailureKind.MALFORMED)
