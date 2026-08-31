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
from typing import TypeVar

from pydantic import BaseModel

from careeros_common import get_logger
from careeros_llm.cli_provider import CLI_SPECS, CliProvider
from careeros_llm.config import LLMConfig
from careeros_llm.exceptions import (
    MalformedResponseError,
    NoProviderAvailableError,
    ProviderCallError,
)
from careeros_llm.models import LLMRun, LLMTask, ProviderHealth, ProviderStatus
from careeros_llm.provider import ApiKeyProvider, LLMProvider
from careeros_llm.structured import parse_structured, repair_prompt, schema_instruction

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

#: How many times ONE provider is re-asked after returning output that failed
#: validation. One repair catches the overwhelmingly common case (a stray
#: sentence, a missing field) without turning a model that cannot follow the
#: schema into a long, expensive loop — the fallback chain handles that.
DEFAULT_MAX_REPAIRS = 1

#: Shown when nothing is configured at all. Names the two ways out rather than
#: reporting the absence, because "no AI provider" is not something a user can
#: act on and "run `claude` and log in" is.
_NO_PROVIDERS_HINT = (
    "no AI provider is configured — set CAREEROS_AI_API_KEY, or install and "
    "log in to one of: " + ", ".join(CLI_SPECS)
)


class LLMResponse:
    """Text plus the provenance of the call that produced it."""

    __slots__ = ("run", "text")

    def __init__(self, text: str, run: LLMRun) -> None:
        self.text = text
        self.run = run

    def __str__(self) -> str:  # so callers can drop it straight into a string
        return self.text


class StructuredResponse[V: BaseModel]:
    """A validated object plus the provenance of the call that produced it."""

    __slots__ = ("run", "value")

    def __init__(self, value: V, run: LLMRun) -> None:
        self.value = value
        self.run = run


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
            raise NoProviderAvailableError(task.value, [_NO_PROVIDERS_HINT])

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

    def complete_structured(
        self,
        *,
        task: LLMTask,
        system: str,
        prompt: str,
        schema: type[T],
        max_repairs: int = DEFAULT_MAX_REPAIRS,
    ) -> StructuredResponse[T]:
        """Run ``task`` and return a validated ``schema`` instance.

        The pipeline is parse → validate → repair → fall back, and it never
        short-circuits: output that does not validate is NEVER handed to a
        caller, because a half-parsed object poisons everything downstream far
        more quietly than a raised error does.

        A provider that returns unusable output is re-asked ``max_repairs``
        times with the validation error quoted back — the one retry that
        reliably helps — and then abandoned for the next provider in the chain.
        Non-retryable failures (not logged in, bad config) skip the repair loop
        entirely: re-asking a CLI that is not authenticated just costs the user
        another timeout.
        """
        chain = self._review_chain(task)
        if not chain:
            raise NoProviderAvailableError(task.value, [_NO_PROVIDERS_HINT])

        full_system = f"{system}{schema_instruction(schema)}"
        reasons: list[str] = []
        for provider in chain:
            started = time.monotonic()
            attempt_prompt = prompt
            retries = 0
            while True:
                try:
                    text = provider.complete(system=full_system, prompt=attempt_prompt)
                except ProviderCallError as exc:
                    reasons.append(str(exc))
                    logger.warning(
                        "LLM provider %s failed for %s: %s", provider.provider_id, task, exc
                    )
                    break
                except Exception as exc:
                    reasons.append(f"{provider.provider_id}: unexpected failure: {exc}")
                    logger.exception("LLM provider %s raised for %s", provider.provider_id, task)
                    break

                try:
                    value = parse_structured(text, schema)
                except ValueError as exc:
                    problem = str(exc)
                    if retries >= max_repairs:
                        reasons.append(
                            str(MalformedResponseError(provider.provider_id, problem))
                            + " (after "
                            + f"{retries} repair attempt{'s' if retries != 1 else ''})"
                        )
                        break
                    retries += 1
                    attempt_prompt = repair_prompt(prompt, text, problem)
                    logger.info(
                        "LLM provider %s returned unusable output for %s (%s) — repairing",
                        provider.provider_id,
                        task,
                        problem,
                    )
                    continue

                return StructuredResponse(
                    value,
                    LLMRun(
                        task=task,
                        provider_id=provider.provider_id,
                        model=provider.model,
                        succeeded=True,
                        fallbacks=list(reasons),
                        duration_ms=int((time.monotonic() - started) * 1000),
                        response_chars=len(text),
                        retries=retries,
                    ),
                )

        raise NoProviderAvailableError(task.value, reasons)

    def try_complete_structured(
        self,
        *,
        task: LLMTask,
        system: str,
        prompt: str,
        schema: type[T],
        max_repairs: int = DEFAULT_MAX_REPAIRS,
    ) -> StructuredResponse[T] | None:
        """``complete_structured`` for callers with a deterministic fallback.

        Returns None rather than raising — and None, never a partially filled
        object, so no caller can mistake a failure for an answer.
        """
        try:
            return self.complete_structured(
                task=task, system=system, prompt=prompt, schema=schema, max_repairs=max_repairs
            )
        except NoProviderAvailableError as exc:
            logger.info("No LLM available for structured %s: %s", task, exc)
            return None

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
                        # The probe itself broke. That is our bug, and calling
                        # it "unavailable" would send the user to fix their
                        # login over a fault that is not theirs.
                        status=ProviderStatus.ERROR,
                        detail=f"health check raised: {exc}",
                        model=provider.model,
                    )
                )
        return results

    def provider_report(self) -> list[ProviderHealth]:
        """Health for every provider CareerOS knows how to use — including the
        ones that are not installed or configured here.

        ``health()`` only covers providers that exist on this machine, which
        answers "what can I use?" but not "why can't I use Codex?". A user
        cannot act on a provider that is silently missing from the list, so
        this one reports the absent ones explicitly, with the reason and the
        command that would change it.
        """
        results = self.health()
        seen = {health.provider_id for health in results}

        import shutil

        for provider_id, spec in CLI_SPECS.items():
            if provider_id in seen:
                continue
            installed = shutil.which(spec.executable) is not None
            if installed:
                # Installed but excluded from the live chain — the only way
                # that happens is CAREEROS_LLM_CLI_ENABLED=0.
                results.append(
                    ProviderHealth(
                        provider_id=provider_id,
                        status=ProviderStatus.NOT_CONFIGURED,
                        detail="agent CLIs are disabled by configuration",
                        installed=True,
                        remedy="unset CAREEROS_LLM_CLI_ENABLED (or set it to 1)",
                    )
                )
            else:
                results.append(
                    ProviderHealth(
                        provider_id=provider_id,
                        status=ProviderStatus.NOT_INSTALLED,
                        detail=f"`{spec.executable}` is not on PATH",
                        installed=False,
                        remedy=spec.install_hint,
                    )
                )

        if not any(health.provider_id not in CLI_SPECS for health in results):
            # No API-key provider was built, i.e. no key is set anywhere.
            results.append(
                ProviderHealth(
                    provider_id="api-key",
                    status=ProviderStatus.NOT_CONFIGURED,
                    detail="no API key configured",
                    remedy="set CAREEROS_AI_API_KEY, or add a key in Settings → AI",
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
