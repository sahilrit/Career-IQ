"""Tests for HttpxArbeitnowTransport, via httpx.MockTransport (no real network)."""

from __future__ import annotations

import httpx
import pytest

from careeros_arbeitnow_provider.client import ARBEITNOW_API_URL, HttpxArbeitnowTransport
from careeros_job_providers import JobProviderError


def _client_returning(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_fetch_returns_the_data_array():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == ARBEITNOW_API_URL
        return httpx.Response(
            200, json={"data": [{"slug": "x", "title": "Engineer"}], "links": {}, "meta": {}}
        )

    transport = HttpxArbeitnowTransport(client=_client_returning(handler))
    data = transport.fetch()
    assert data == [{"slug": "x", "title": "Engineer"}]


def test_fetch_sends_a_user_agent_header():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["user_agent"] = request.headers.get("user-agent")
        return httpx.Response(200, json={"data": []})

    HttpxArbeitnowTransport(client=_client_returning(handler)).fetch()
    assert "CareerOS" in captured["user_agent"]


def test_fetch_raises_job_provider_error_on_http_error_status():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "unavailable"})

    transport = HttpxArbeitnowTransport(client=_client_returning(handler))
    with pytest.raises(JobProviderError):
        transport.fetch()


def test_fetch_raises_job_provider_error_when_data_key_missing():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": "shape"})

    transport = HttpxArbeitnowTransport(client=_client_returning(handler))
    with pytest.raises(JobProviderError):
        transport.fetch()


def test_fetch_raises_job_provider_error_when_data_is_not_a_list():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": "not-a-list"})

    transport = HttpxArbeitnowTransport(client=_client_returning(handler))
    with pytest.raises(JobProviderError):
        transport.fetch()
