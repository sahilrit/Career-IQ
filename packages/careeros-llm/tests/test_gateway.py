"""LLMGateway: routing, fallback, honesty about failure."""

from __future__ import annotations

import pytest

from careeros_llm import (
    LLMConfig,
    LLMGateway,
    LLMTask,
    NoProviderAvailableError,
    ProviderCallError,
    ProviderHealth,
    ProviderStatus,
)


class StubProvider:
    """A provider that answers, or fails, on command."""

    def __init__(self, provider_id: str, *, answer: str | None = None, fails: str | None = None):
        self._id = provider_id
        self._answer = answer
        self._fails = fails
        self.calls: list[tuple[str, str]] = []

    @property
    def provider_id(self) -> str:
        return self._id

    @property
    def model(self) -> str:
        return f"{self._id}-model"

    def complete(self, *, system: str, prompt: str) -> str:
        self.calls.append((system, prompt))
        if self._fails:
            raise ProviderCallError(self._id, self._fails)
        return self._answer or ""

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_id=self._id,
            status=ProviderStatus.UNAVAILABLE if self._fails else ProviderStatus.HEALTHY,
            detail=self._fails or "",
            model=self.model,
        )


def gateway(providers, **config_kwargs) -> LLMGateway:
    config = LLMConfig(priority=[p.provider_id for p in providers], **config_kwargs)
    return LLMGateway(providers, config=config)


class TestFallback:
    def test_first_healthy_provider_answers(self):
        first = StubProvider("a", answer="from-a")
        second = StubProvider("b", answer="from-b")
        response = gateway([first, second]).complete(task=LLMTask.WRITE, system="s", prompt="p")
        assert response.text == "from-a"
        assert second.calls == []

    def test_falls_through_to_the_next_provider(self):
        first = StubProvider("a", fails="rate limited")
        second = StubProvider("b", answer="from-b")
        response = gateway([first, second]).complete(task=LLMTask.WRITE, system="s", prompt="p")
        assert response.text == "from-b"
        assert response.run.provider_id == "b"
        # The failure is recorded, not hidden.
        assert any("rate limited" in f for f in response.run.fallbacks)

    def test_walks_the_whole_chain(self):
        providers = [
            StubProvider("a", fails="down"),
            StubProvider("b", fails="down"),
            StubProvider("c", answer="from-c"),
        ]
        assert (
            gateway(providers).complete(task=LLMTask.WRITE, system="s", prompt="p").text == "from-c"
        )

    def test_every_provider_failing_raises_with_all_reasons(self):
        providers = [StubProvider("a", fails="no key"), StubProvider("b", fails="not logged in")]
        with pytest.raises(NoProviderAvailableError) as exc:
            gateway(providers).complete(task=LLMTask.WRITE, system="s", prompt="p")
        message = str(exc.value)
        assert "no key" in message and "not logged in" in message

    def test_no_providers_at_all_names_the_fix(self):
        with pytest.raises(NoProviderAvailableError) as exc:
            LLMGateway([], config=LLMConfig()).complete(task=LLMTask.WRITE, system="s", prompt="p")
        assert "CAREEROS_AI_API_KEY" in str(exc.value)

    def test_never_returns_a_fabricated_answer_on_total_failure(self):
        # The regression this guards: a gateway that "helpfully" returns "" or a
        # placeholder would let a caller submit an empty application answer as
        # if it had been generated.
        providers = [StubProvider("a", fails="down")]
        with pytest.raises(NoProviderAvailableError):
            gateway(providers).complete(task=LLMTask.ANSWER, system="s", prompt="p")

    def test_an_unexpected_exception_does_not_break_the_chain(self):
        class Exploding(StubProvider):
            def complete(self, *, system: str, prompt: str) -> str:
                raise RuntimeError("kaboom")

        providers = [Exploding("a"), StubProvider("b", answer="from-b")]
        assert (
            gateway(providers).complete(task=LLMTask.WRITE, system="s", prompt="p").text == "from-b"
        )


class TestTryComplete:
    def test_returns_none_instead_of_raising(self):
        assert (
            gateway([StubProvider("a", fails="down")]).try_complete(
                task=LLMTask.WRITE, system="s", prompt="p"
            )
            is None
        )

    def test_returns_the_response_when_one_works(self):
        result = gateway([StubProvider("a", answer="hi")]).try_complete(
            task=LLMTask.WRITE, system="s", prompt="p"
        )
        assert result is not None and result.text == "hi"


class TestRouting:
    def test_task_pin_wins_over_priority_order(self):
        first = StubProvider("a", answer="from-a")
        second = StubProvider("b", answer="from-b")
        config = LLMConfig(priority=["a", "b"], task_routing={LLMTask.CLASSIFY: "b"})
        response = LLMGateway([first, second], config=config).complete(
            task=LLMTask.CLASSIFY, system="s", prompt="p"
        )
        assert response.text == "from-b"

    def test_a_pinned_provider_still_falls_back_when_it_fails(self):
        # Pinning is a preference, not a single point of failure.
        pinned = StubProvider("b", fails="down")
        other = StubProvider("a", answer="from-a")
        config = LLMConfig(priority=["a", "b"], task_routing={LLMTask.CLASSIFY: "b"})
        assert (
            LLMGateway([other, pinned], config=config)
            .complete(task=LLMTask.CLASSIFY, system="s", prompt="p")
            .text
            == "from-a"
        )

    def test_review_prefers_a_different_provider_than_the_drafter(self):
        drafter = StubProvider("a", answer="from-a")
        reviewer = StubProvider("b", answer="from-b")
        gw = gateway([drafter, reviewer])
        assert gw.complete(task=LLMTask.WRITE, system="s", prompt="p").text == "from-a"
        assert gw.complete(task=LLMTask.REVIEW, system="s", prompt="p").text == "from-b"

    def test_review_still_happens_with_only_one_provider(self):
        # A same-model review is worth more than no review.
        only = StubProvider("a", answer="reviewed")
        assert (
            gateway([only]).complete(task=LLMTask.REVIEW, system="s", prompt="p").text == "reviewed"
        )

    def test_a_provider_absent_from_priority_is_still_a_last_resort(self):
        listed = StubProvider("a", fails="down")
        unlisted = StubProvider("z", answer="from-z")
        config = LLMConfig(priority=["a"])
        assert (
            LLMGateway([listed, unlisted], config=config)
            .complete(task=LLMTask.WRITE, system="s", prompt="p")
            .text
            == "from-z"
        )


class TestHealth:
    def test_reports_every_provider(self):
        health = gateway(
            [StubProvider("a", answer="x"), StubProvider("b", fails="not logged in")]
        ).health()
        by_id = {h.provider_id: h for h in health}
        assert by_id["a"].status is ProviderStatus.HEALTHY
        assert by_id["b"].status is ProviderStatus.UNAVAILABLE
        assert "not logged in" in by_id["b"].detail

    def test_a_raising_probe_becomes_a_status_not_a_crash(self):
        class BadProbe(StubProvider):
            def health_check(self):
                raise RuntimeError("probe exploded")

        health = gateway([BadProbe("a")]).health()
        # ERROR, not UNAVAILABLE: a probe that crashes is a CareerOS bug, and
        # reporting it as "the provider is unavailable" sends the user off to
        # fix a login that was never broken.
        assert health[0].status is ProviderStatus.ERROR
        assert "probe exploded" in health[0].detail

    def test_is_configured_reflects_provider_presence(self):
        assert gateway([StubProvider("a", answer="x")]).is_configured
        assert not LLMGateway([], config=LLMConfig()).is_configured


class TestRunRecord:
    def test_records_provenance_without_the_prompt(self):
        response = gateway([StubProvider("a", answer="hello there")]).complete(
            task=LLMTask.WRITE, system="secret profile facts", prompt="secret prompt"
        )
        run = response.run
        assert run.provider_id == "a"
        assert run.model == "a-model"
        assert run.succeeded and run.response_chars == len("hello there")
        # The candidate's profile must not leak into the observability record.
        assert "secret" not in run.model_dump_json()
