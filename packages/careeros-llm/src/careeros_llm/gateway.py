"""LLMGateway: the single seam between CareerOS business logic and any model.

Callers ask for a *task* ("write this cover letter", "review this draft") and
the gateway decides which provider serves it, retries down a fallback chain
when one fails, and records what actually happened.

Three rules it never breaks:

* **Never fabricate.** If every provider fails, it raises
  ``NoProviderAvailableError`` with the per-provider reasons. It does not
  return an empty string, a canned sentence, or a placeholder that a caller
  could mistake for a real answer.
* **Never retry blindly across a side effect.** The gateway only ever performs
  text completion, which is safe to retry. Browser and submission side effects
  live elsewhere and are deliberately not routed through here.
* **Always say which model spoke.** Every call returns an ``LLMRun`` alongside
  the text so a generated answer can be traced to its source.
"""

from __future__ import annotations

import time

from careeros_common import get_logger
from careeros_llm.cli_provider import CLI_SPECS, CliProvider
from careeros_llm.config import LLMConfig
from careeros_llm.exceptions import NoProviderAvailableError, ProviderCallError
from careeros_llm.models import LLMRun, LLMTask, ProviderHealth, ProviderStatus
from careeros_llm.provider import ApiKeyProvider, LLMProvider

logger = get_logger(__name__)


class LLMResponse:
    """Text plus the provenance of the call that produced it."""

    __slots__ = ("run", "text")

    def __init__(self, text: str, run: LLMRun) -> None:
        self.text = text
        self.run = run

    def __str__(self) -> str:  # so callers can drop it straight into a string
        return self.text


class LLMGateway:
    def __init__(
        self,
        providers: list[LLMProvider] | None = None,
        *,
        config: LLMConfig | None = None,
    ) -> None:
        self._config = config or LLMConfig()
        self._providers: list[LLMProvider] = (
            list(providers) if providers is not None else build_providers(self._config)
        )

    # -- construction -------------------------------------------------------

    @classmethod
    def from_env(cls, **overrides) -> LLMGateway:
        config = LLMConfig.from_env(**overrides)
        return cls(config=config)

    @property
    def config(self) -> LLMConfig:
        return self._config

    def providers(self) -> list[LLMProvider]:
        return list(self._providers)

    @property
    def is_configured(self) -> bool:
        """At least one provider exists. Says nothing about whether it works —
        that is ``health()``. Callers use this to decide whether to offer an
        AI-backed path at all."""
        return bool(self._providers)

    # -- routing ------------------------------------------------------------

    def _chain_for(self, task: LLMTask) -> list[LLMProvider]:
        """Providers to try for ``task``, best first.

        Order: the task's pinned provider (if configured and present), then
        everything else in configured priority order, then anything not named
        in the priority list at all — so an unlisted provider is a last resort
        rather than invisible.
        """
        by_id = {p.provider_id: p for p in self._providers}
        chain: list[LLMProvider] = []
        seen: set[str] = set()

        def push(provider: LLMProvider | None) -> None:
            if provider is not None and provider.provider_id not in seen:
                seen.add(provider.provider_id)
                chain.append(provider)

        pinned = self._config.task_routing.get(task)
        if pinned:
            push(by_id.get(pinned))
        for provider_id in self._config.priority:
            push(by_id.get(provider_id))
        for provider in self._providers:
            push(provider)
        return chain

    def _review_chain(self, task: LLMTask) -> list[LLMProvider]:
        """REVIEW prefers a provider other than the one that drafts.

        An independent reviewer is the point of the drafter/reviewer split; a
        reviewer running on the same model as the drafter shares its blind
        spots. When only one provider exists we still review — a same-model
        review catches plenty (dates, fabricated employers, missing fields) and
        is strictly better than no review — but a different one wins if there
        is one.
        """
        chain = self._chain_for(task)
        if task is not LLMTask.REVIEW or len(chain) < 2:
            return chain
        drafter = self._chain_for(LLMTask.WRITE)
        drafter_id = drafter[0].provider_id if drafter else None
        if drafter_id is None:
            return chain
        others = [p for p in chain if p.provider_id != drafter_id]
        same = [p for p in chain if p.provider_id == drafter_id]
        return others + same

    # -- the call ------------------------------------------------------------

    def complete(self, *, task: LLMTask, system: str, prompt: str) -> LLMResponse:
        """Run ``task``, walking the fallback chain until one provider answers.

        Raises ``NoProviderAvailableError`` when none does — never returns a
        placeholder.
        """
        chain = self._review_chain(task)
        if not chain:
            raise NoProviderAvailableError(
                task.value,
                [
                    "no AI provider is configured — set CAREEROS_AI_API_KEY, or install and "
                    "log in to one of: " + ", ".join(CLI_SPECS)
                ],
            )

        reasons: list[str] = []
        for provider in chain:
            started = time.monotonic()
            try:
                text = provider.complete(system=system, prompt=prompt)
            except ProviderCallError as exc:
                reasons.append(str(exc))
                logger.warning("LLM provider %s failed for %s: %s", provider.provider_id, task, exc)
                continue
            except Exception as exc:
                reasons.append(f"{provider.provider_id}: unexpected failure: {exc}")
                logger.exception("LLM provider %s raised for %s", provider.provider_id, task)
                continue
            duration_ms = int((time.monotonic() - started) * 1000)
            run = LLMRun(
                task=task,
                provider_id=provider.provider_id,
                model=provider.model,
                succeeded=True,
                fallbacks=list(reasons),
                duration_ms=duration_ms,
                response_chars=len(text),
            )
            return LLMResponse(text, run)

        raise NoProviderAvailableError(task.value, reasons)

    def try_complete(self, *, task: LLMTask, system: str, prompt: str) -> LLMResponse | None:
        """``complete`` for callers with a real deterministic fallback of their
        own (a template cover letter, a rule-based answer).

        Returns None instead of raising. This is the ONLY sanctioned way to
        treat "no AI" as non-fatal, and it hands back None — not text — so a
        caller cannot accidentally present a failure as a generated answer.
        """
        try:
            return self.complete(task=task, system=system, prompt=prompt)
        except NoProviderAvailableError as exc:
            logger.info("No LLM available for %s: %s", task, exc)
            return None

    # -- health --------------------------------------------------------------

    def health(self) -> list[ProviderHealth]:
        """Probe every provider. Ordered best-first so the first HEALTHY entry
        is the one that would actually serve a default call."""
        ordered = self._chain_for(LLMTask.WRITE)
        results: list[ProviderHealth] = []
        for provider in ordered:
            try:
                results.append(provider.health_check())
            except Exception as exc:
                results.append(
                    ProviderHealth(
                        provider_id=provider.provider_id,
                        status=ProviderStatus.UNAVAILABLE,
                        detail=f"health check raised: {exc}",
                        model=provider.model,
                    )
                )
        return results


def build_providers(config: LLMConfig) -> list[LLMProvider]:
    """Every provider this machine/config can offer, unprobed.

    Construction is cheap and never touches the network — health checks do.
    """
    providers: list[LLMProvider] = []
    if config.api_key:
        providers.append(ApiKeyProvider(config.api_key, model=config.api_model))
    if config.cli_enabled:
        import shutil

        for spec in CLI_SPECS.values():
            if shutil.which(spec.executable) is not None:
                providers.append(CliProvider(spec, timeout_seconds=config.cli_timeout_seconds))
    return providers
