from careeros_api.ai_support import (
    delete_workspace_key,
    has_workspace_key,
    reset_gateway_cache,
    resolve_cover_letter_generator,
    store_workspace_key,
)
from careeros_application_engine import AICoverLetterGenerator
from careeros_common import open_store
from careeros_llm import ApiKeyProvider, GatewayAIClient, LLMTask


def test_key_round_trip_and_generator_selection(tmp_path, monkeypatch):
    monkeypatch.setenv("CAREEROS_DATA_DIR", str(tmp_path))
    reset_gateway_cache()  # gateways are cached per key; start from nothing
    store = open_store()

    assert has_workspace_key(store, "ws1") is False
    assert resolve_cover_letter_generator(store, "ws1") is None

    store_workspace_key(store, "ws1", "sk-ant-abc")
    assert has_workspace_key(store, "ws1") is True

    generator = resolve_cover_letter_generator(store, "ws1")
    assert isinstance(generator, AICoverLetterGenerator)
    # The client is the gateway, not a raw vendor client — every AI call in
    # CareerOS goes through one seam so it gets fallback and provenance. The
    # workspace's own key is still what it reaches for first.
    assert isinstance(generator._client, GatewayAIClient)
    chain = generator._client._gateway._chain_for(LLMTask.WRITE)
    assert chain[0].provider_id == "anthropic"
    assert isinstance(chain[0], ApiKeyProvider)

    delete_workspace_key(store, "ws1")
    assert has_workspace_key(store, "ws1") is False
    assert resolve_cover_letter_generator(store, "ws1") is None


def test_keys_are_workspace_isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("CAREEROS_DATA_DIR", str(tmp_path))
    store = open_store()
    store_workspace_key(store, "ws1", "sk-ant-one")
    assert has_workspace_key(store, "ws1") is True
    assert has_workspace_key(store, "ws2") is False


def test_arbitrary_secret_key_env_works(tmp_path, monkeypatch):
    # Render's generateValue is a plain random string, not a Fernet key —
    # the cipher must still round-trip.
    monkeypatch.setenv("CAREEROS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("CAREEROS_SECRET_KEY", "some-random-render-value-xyz")
    store = open_store()
    store_workspace_key(store, "ws1", "sk-ant-secret")
    assert resolve_cover_letter_generator(store, "ws1") is not None
