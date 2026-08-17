import httpx
import pytest

from careeros_ai import AIAuthError, AIUnavailableError, AnthropicClient


def _transport(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_complete_returns_text():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-api-key"] == "sk-ant-test"
        assert request.headers["anthropic-version"]
        return httpx.Response(200, json={"content": [{"type": "text", "text": "Dear Team,"}]})

    client = AnthropicClient("sk-ant-test", http_client=_transport(handler))
    assert client.complete(system="s", prompt="p") == "Dear Team,"


def test_401_raises_auth_error():
    client = AnthropicClient(
        "bad", http_client=_transport(lambda r: httpx.Response(401, json={"error": {}}))
    )
    with pytest.raises(AIAuthError):
        client.complete(system="s", prompt="p")


def test_500_raises_unavailable():
    client = AnthropicClient(
        "sk-ant-x", http_client=_transport(lambda r: httpx.Response(529, json={}))
    )
    with pytest.raises(AIUnavailableError):
        client.complete(system="s", prompt="p")
