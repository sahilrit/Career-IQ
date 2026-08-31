"""AI resolution when the workspace has no API key.

This is the case the zero-paid-API design exists for and the one it used to
fail: every AI feature resolved to None, so a user running CareerOS locally
with a Claude subscription got templates and no explanation.
"""

from __future__ import annotations

import pytest

from careeros_ai import AIUnavailableError
from careeros_api.ai_support import (
    ai_source,
    reset_gateway_cache,
    resolve_ai_client,
    resolve_cover_letter_generator,
    resolve_llm_job_scorer,
    store_workspace_key,
)
from careeros_common import open_store
from careeros_llm import (
    GatewayAIClient,
    LLMConfig,
    LLMGateway,
    LLMTask,
    ProviderHealth,
    ProviderStatus,
)


class StubProvider:
    def __init__(self, provider_id="stub", answer="generated text", fails=None):
        self._id, self._answer, self._fails = provider_id, answer, fails

    @property
    def provider_id(self):
        return self._id

    @property
    def model(self):
        return "stub-model"

    def complete(self, *, system, prompt):
        if self._fails:
            from careeros_llm import ProviderCallError

            raise ProviderCallError(self._id, self._fails)
        return self._answer

    def health_check(self):
        return ProviderHealth(provider_id=self._id, status=ProviderStatus.HEALTHY)


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CAREEROS_DATA_DIR", str(tmp_path))
    return open_store()


@pytest.fixture
def with_local_provider(monkeypatch):
    """Pretend this machine has one working local provider."""
    gateway = LLMGateway([StubProvider()], config=LLMConfig(priority=["stub"]))
    monkeypatch.setattr("careeros_api.ai_support._gateway", gateway)
    yield gateway
    reset_gateway_cache()


class TestWithNoProviderAtAll:
    def test_everything_resolves_to_none(self, store, monkeypatch):
        monkeypatch.setenv("CAREEROS_LLM_CLI_ENABLED", "0")
        reset_gateway_cache()
        assert resolve_ai_client(store, "ws1") is None
        assert resolve_cover_letter_generator(store, "ws1") is None
        assert resolve_llm_job_scorer(store, "ws1") is None

    def test_the_settings_label_says_so_plainly(self, store, monkeypatch):
        monkeypatch.setenv("CAREEROS_LLM_CLI_ENABLED", "0")
        reset_gateway_cache()
        assert ai_source(store, "ws1") == "not configured"


class TestWithALocalProviderAndNoKey:
    def test_ai_features_come_on(self, store, with_local_provider):
        assert resolve_ai_client(store, "ws1") is not None
        assert resolve_cover_letter_generator(store, "ws1") is not None
        assert resolve_llm_job_scorer(store, "ws1") is not None

    def test_the_client_actually_generates(self, store, with_local_provider):
        client = resolve_ai_client(store, "ws1")
        assert client.complete(system="s", prompt="p") == "generated text"

    def test_the_settings_label_names_the_source(self, store, with_local_provider):
        assert "locally authenticated" in ai_source(store, "ws1")
        assert "stub" in ai_source(store, "ws1")

    def test_the_scorer_is_routed_as_an_analysis_task(self, store, with_local_provider):
        # Scoring is high-volume; routing it separately is what lets a cheaper
        # model be pinned to it without touching the writing tasks.
        scorer = resolve_llm_job_scorer(store, "ws1")
        client = scorer._client
        assert isinstance(client, GatewayAIClient)
        assert client._task is LLMTask.ANALYZE


class TestAWorkspaceKeyWins:
    def test_the_key_is_preferred_over_a_local_provider(self, store, with_local_provider):
        # An explicit key is faster and is the only thing that works on a
        # hosted server, so it must not be shadowed by a local CLI.
        store_workspace_key(store, "ws1", "sk-ant-test")
        client = resolve_ai_client(store, "ws1")
        chain = client._gateway._chain_for(LLMTask.WRITE)
        assert chain[0].provider_id == "anthropic"
        assert "your API key" in ai_source(store, "ws1")

    def test_the_key_still_has_the_fallback_chain_behind_it(self, store, with_local_provider):
        # The key used to be turned into a raw vendor client, so a workspace
        # WITH a key had no fallback at all: a rate-limited key failed the
        # feature outright, on a machine with a working CLI sitting right
        # there. The key wins, but it is no longer a dead end.
        store_workspace_key(store, "ws1", "sk-ant-test")
        client = resolve_ai_client(store, "ws1")
        assert isinstance(client, GatewayAIClient)
        ids = [p.provider_id for p in client._gateway._chain_for(LLMTask.WRITE)]
        assert "anthropic" in ids and "stub" in ids
        assert ids.index("anthropic") < ids.index("stub")


class TestFailureIsNeverFabrication:
    def test_a_dead_provider_raises_rather_than_returning_text(self, store, monkeypatch):
        gateway = LLMGateway(
            [StubProvider(fails="not logged in")], config=LLMConfig(priority=["stub"])
        )
        monkeypatch.setattr("careeros_api.ai_support._gateway", gateway)
        client = resolve_ai_client(store, "ws1")
        # Surfaced as the AI layer's own unavailable error, which every caller
        # already handles by falling back to its deterministic template. The
        # caller never receives an invented string.
        with pytest.raises(AIUnavailableError, match="not logged in"):
            client.complete(system="s", prompt="p")
        reset_gateway_cache()
