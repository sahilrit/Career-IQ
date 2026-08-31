"""GatewayAIClient: the gateway wearing the ``AIClient`` interface.

Every AI feature in CareerOS already talks to ``careeros_ai.AIClient`` —
strings in, strings out. Rather than rewrite each of those call sites, the
gateway is exposed through that same interface, so a feature written against
one Anthropic key now gets provider fallback, task routing and CLI providers
for free and without changing.

The important consequence is for a user with NO API key. Every AI feature
previously resolved to None for them and silently degraded to templates. If
they have `claude` or `gemini` authenticated locally, the gateway is a working
provider, and those features come on.
"""

from __future__ import annotations

from careeros_ai import AIUnavailableError
from careeros_llm.exceptions import NoProviderAvailableError
from careeros_llm.gateway import LLMGateway
from careeros_llm.models import LLMRun, LLMTask


class GatewayAIClient:
    """An ``AIClient`` backed by the gateway, pinned to one task."""

    def __init__(self, gateway: LLMGateway, task: LLMTask = LLMTask.WRITE) -> None:
        self._gateway = gateway
        self._task = task
        #: Provenance of the calls made through this client, newest last. Lets
        #: a caller record which model wrote a given cover letter without
        #: threading a return value through code that expects a plain string.
        self.runs: list[LLMRun] = []

    def complete(self, *, system: str, prompt: str) -> str:
        try:
            response = self._gateway.complete(task=self._task, system=system, prompt=prompt)
        except NoProviderAvailableError as exc:
            # Raised as the AI layer's own "transient/unavailable" error, which
            # existing callers already handle by falling back to their
            # deterministic template. They never receive a fabricated string.
            raise AIUnavailableError(str(exc)) from exc
        self.runs.append(response.run)
        return response.text

    @property
    def last_run(self) -> LLMRun | None:
        return self.runs[-1] if self.runs else None


def client_for(gateway: LLMGateway, task: LLMTask = LLMTask.WRITE) -> GatewayAIClient:
    return GatewayAIClient(gateway, task)
