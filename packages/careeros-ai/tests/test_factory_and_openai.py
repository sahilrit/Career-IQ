import httpx
import pytest

from careeros_ai import (
    AIAuthError,
    AIUnavailableError,
    AnthropicClient,
    OpenAICompatibleClient,
    build_client,
    provider_for_key,
)


def _transport(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_provider_detection():
    assert provider_for_key("sk-ant-abc") == "anthropic"
    assert provider_for_key("sk-or-v1-abc") == "openrouter"
    assert provider_for_key("sk-abc123") == "openai"


def test_build_client_picks_the_right_client():
    assert isinstance(build_client("sk-ant-xxxxxxxxxxxx"), AnthropicClient)
    assert isinstance(build_client("sk-or-v1-xxxxxxxx"), OpenAICompatibleClient)
    assert isinstance(build_client("sk-openai-xxxxxxxx"), OpenAICompatibleClient)


def test_openrouter_client_hits_openrouter_and_parses():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "openrouter.ai" in str(request.url)
        assert request.headers["authorization"] == "Bearer sk-or-v1-test"
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "Hello from OpenRouter"}}]}
        )

    client = build_client("sk-or-v1-test", http_client=_transport(handler))
    assert client.complete(system="s", prompt="p") == "Hello from OpenRouter"


def test_openai_compatible_401_and_500():
    auth = OpenAICompatibleClient(
        "sk-bad",
        "gpt-4o-mini",
        "https://api.openai.com/v1",
        http_client=_transport(lambda r: httpx.Response(401, json={})),
    )
    with pytest.raises(AIAuthError):
        auth.complete(system="s", prompt="p")

    down = OpenAICompatibleClient(
        "sk-x",
        "gpt-4o-mini",
        "https://api.openai.com/v1",
        http_client=_transport(lambda r: httpx.Response(503, json={})),
    )
    with pytest.raises(AIUnavailableError):
        down.complete(system="s", prompt="p")
