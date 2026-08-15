"""Thin HTTP client for RemoteOK's public JSON API.

RemoteOK's job feed (``https://remoteok.com/api``) requires no API key
and no paid plan — it's a plain public JSON endpoint. This wraps it
behind a small ``RemoteOKTransport`` interface so the provider can be
tested against fixture data without ever making a real network call; see
``tests/conftest.py`` for the fake used by provider/parser tests, and
``tests/test_client.py`` for testing ``HttpxRemoteOKTransport`` itself via
``httpx.MockTransport`` (still zero real network calls).
"""

from __future__ import annotations

from typing import Any, Protocol

import httpx

from careeros_job_providers import JobProviderError

REMOTEOK_API_URL = "https://remoteok.com/api"
USER_AGENT = "CareerOS/0.1 (+https://github.com/careeros; job-discovery bot)"


class RemoteOKTransport(Protocol):
    def fetch(self) -> list[dict[str, Any]]: ...


class HttpxRemoteOKTransport:
    """Real transport: a GET request against RemoteOK's public API.

    Accepts an optional pre-built ``httpx.Client`` so tests can inject one
    backed by ``httpx.MockTransport`` instead of touching the network.
    """

    def __init__(
        self,
        *,
        base_url: str = REMOTEOK_API_URL,
        timeout: float = 10.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout)

    def fetch(self) -> list[dict[str, Any]]:
        try:
            response = self._client.get(self._base_url, headers={"User-Agent": USER_AGENT})
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise JobProviderError(f"RemoteOK request failed: {exc}") from exc
        if not isinstance(data, list):
            raise JobProviderError("RemoteOK response was not a JSON array")
        return data

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
