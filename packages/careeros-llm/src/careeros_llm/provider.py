"""The provider contract behind the gateway.

Two concrete kinds ship today:

* ``ApiKeyProvider``  — an HTTP API reached with a key (Anthropic, OpenAI,
  Gemini, Groq, OpenRouter, NVIDIA), built on the existing ``careeros_ai``
  client so nothing about that layer had to be rewritten.
* ``CliProvider``     — a locally authenticated agent CLI (`claude`, `codex`,
  `gemini`). This is what makes the zero-paid-API promise real: a user with a
  Claude or Gemini subscription already has working AI on their machine and
  never has to buy an API key.

Both satisfy the same ``LLMProvider`` protocol, so the gateway does not know
or care which is serving a call.
"""

from __future__ import annotations

from typing import Protocol

from careeros_ai import (
    AIAuthError,
    AIClient,
    AIUnavailableError,
    build_client,
    default_model_for_key,
)
from careeros_common import get_logger
from careeros_llm.exceptions import ProviderCallError
from careeros_llm.models import (
    FailureKind,
    ProviderHealth,
    ProviderStatus,
    status_for_failure,
)

logger = get_logger(__name__)

#: A probe must be trivially cheap — it exists to prove auth works, not to
#: measure quality.
_PROBE_SYSTEM = "You are a health probe. Reply with exactly one word."
_PROBE_PROMPT = "Reply with exactly: OK"


class LLMProvider(Protocol):
    @property
    def provider_id(self) -> str: ...

    @property
    def model(self) -> str: ...

    def complete(self, *, system: str, prompt: str) -> str: ...

    def health_check(self) -> ProviderHealth: ...


class ApiKeyProvider:
    """An HTTP LLM API reached with a key.

    The key's *shape* picks the vendor (``careeros_ai.build_client``), so the
    user pastes one key and it works — no separate "which provider" setting to
    get wrong.
    """

    def __init__(
        self,
        api_key: str,
        *,
        model: str | None = None,
        provider_id: str | None = None,
        client: AIClient | None = None,
    ) -> None:
        self._api_key = api_key.strip()
        self._model = model or (default_model_for_key(self._api_key) if self._api_key else "")
        self._client = client
        if provider_id:
            self._provider_id = provider_id
        else:
            from careeros_ai import provider_for_key

            self._provider_id = provider_for_key(self._api_key) if self._api_key else "api"

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def model(self) -> str:
        return self._model

    def _get_client(self) -> AIClient:
        if self._client is None:
            self._client = build_client(self._api_key, self._model)
        return self._client

    def complete(self, *, system: str, prompt: str) -> str:
        try:
            return self._get_client().complete(system=system, prompt=prompt)
        except AIAuthError as exc:
            raise ProviderCallError(
                self.provider_id, str(exc), kind=FailureKind.NOT_AUTHENTICATED
            ) from exc
        except AIUnavailableError as exc:
            # The AI layer raises this for both transient outages and rate
            # limits, so let the message decide rather than assuming either.
            raise ProviderCallError(self.provider_id, str(exc)) from exc
        except Exception as exc:  # a transport we did not anticipate
            raise ProviderCallError(self.provider_id, f"unexpected failure: {exc}") from exc

    def health_check(self) -> ProviderHealth:
        if not self._api_key:
            return ProviderHealth(
                provider_id=self.provider_id,
                status=ProviderStatus.NOT_CONFIGURED,
                detail="no API key configured",
                model=self._model,
                # A hosted API is never "installed"; saying False would read as
                # a missing package the user could go and install.
                installed=None,
                authenticated=None,
                remedy="set CAREEROS_AI_API_KEY, or add a key in Settings → AI",
            )
        try:
            # Through our own ``complete`` so the probe classifies failures
            # exactly the way a real call would — one code path, one verdict.
            self.complete(system=_PROBE_SYSTEM, prompt=_PROBE_PROMPT)
        except ProviderCallError as exc:
            if exc.kind is FailureKind.NOT_AUTHENTICATED:
                return ProviderHealth(
                    provider_id=self.provider_id,
                    status=ProviderStatus.NOT_AUTHENTICATED,
                    detail=f"the API key was rejected ({exc.detail})",
                    model=self._model,
                    authenticated=False,
                    remedy="check CAREEROS_AI_API_KEY, or replace the key in Settings → AI",
                )
            return ProviderHealth(
                provider_id=self.provider_id,
                status=status_for_failure(exc.kind),
                detail=exc.detail,
                model=self._model,
                authenticated=None,
            )
        except Exception as exc:
            return ProviderHealth(
                provider_id=self.provider_id,
                status=ProviderStatus.UNAVAILABLE,
                detail=f"probe failed: {exc}",
                model=self._model,
                authenticated=None,
            )
        return ProviderHealth(
            provider_id=self.provider_id,
            status=ProviderStatus.AVAILABLE,
            model=self._model,
            authenticated=True,
        )
