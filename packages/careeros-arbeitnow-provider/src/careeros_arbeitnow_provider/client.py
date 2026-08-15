"""Thin HTTP client for Arbeitnow's public job board API.

Arbeitnow's job feed (``https://www.arbeitnow.com/api/job-board-api``)
requires no API key and no paid plan — it's a plain public JSON
endpoint, returning ``{"data": [...], "links": {...}, "meta": {...}}``.
Wrapped behind the same small transport-Protocol shape as
``careeros_remoteok_provider.client`` so the provider is testable
against fixture data without ever making a real network call.
"""

from __future__ import annotations

from typing import Any, Protocol

import httpx

from careeros_job_providers import JobProviderError

ARBEITNOW_API_URL = "https://www.arbeitnow.com/api/job-board-api"
USER_AGENT = "CareerOS/0.1 (+https://github.com/careeros; job-discovery bot)"


class ArbeitnowTransport(Protocol):
    def fetch(self) -> list[dict[str, Any]]: ...


class HttpxArbeitnowTransport:
    """Real transport: a GET request against Arbeitnow's public API.

    Accepts an optional pre-built ``httpx.Client`` so tests can inject one
    backed by ``httpx.MockTransport`` instead of touching the network.
    """

    def __init__(
        self,
        *,
        base_url: str = ARBEITNOW_API_URL,
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
            raise JobProviderError(f"Arbeitnow request failed: {exc}") from exc
        if not isinstance(data, dict) or not isinstance(data.get("data"), list):
            raise JobProviderError("Arbeitnow response did not contain a 'data' array")
        return data["data"]

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
