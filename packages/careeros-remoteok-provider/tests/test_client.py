"""Tests for HttpxRemoteOKTransport, via httpx.MockTransport (no real network)."""

from __future__ import annotations

import httpx
import pytest

from careeros_job_providers import JobProviderError
from careeros_remoteok_provider.client import REMOTEOK_API_URL, HttpxRemoteOKTransport


def _client_returning(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_fetch_returns_parsed_json_array():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == REMOTEOK_API_URL
        return httpx.Response(200, json=[{"legal": "x"}, {"id": "1", "position": "Engineer"}])

    transport = HttpxRemoteOKTransport(client=_client_returning(handler))
    data = transport.fetch()
    assert data == [{"legal": "x"}, {"id": "1", "position": "Engineer"}]


def test_fetch_sends_a_user_agent_header():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["user_agent"] = request.headers.get("user-agent")
        return httpx.Response(200, json=[])

    HttpxRemoteOKTransport(client=_client_returning(handler)).fetch()
    assert "CareerOS" in captured["user_agent"]


def test_fetch_raises_job_provider_error_on_http_error_status():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "unavailable"})

    transport = HttpxRemoteOKTransport(client=_client_returning(handler))
    with pytest.raises(JobProviderError):
        transport.fetch()


def test_fetch_raises_job_provider_error_when_response_is_not_a_list():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": "shape"})

    transport = HttpxRemoteOKTransport(client=_client_returning(handler))
    with pytest.raises(JobProviderError):
        transport.fetch()
