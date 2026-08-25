"""HTTP transport for Seek's public search API.

No key needed — a plain GET with a normal User-Agent is enough (verified
live 2026-08-26). The direct job-posting pages ARE bot-gated, but that's
irrelevant here: the search API itself, which is all this provider calls,
is open.
"""

from __future__ import annotations

from typing import Protocol

import httpx

from careeros_seek_provider.parser import API_URL

USER_AGENT = "CareerOS/0.1 (+https://github.com/careeros; job-discovery bot)"


class SeekTransport(Protocol):
    def search(self, *, keywords: str, location: str | None, page: int) -> str:
        """Fetch one page of results, returning the raw JSON response body."""
        ...


class HttpxSeekTransport:
    def __init__(self, *, timeout: float = 15.0, client: httpx.Client | None = None) -> None:
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout)

    def search(self, *, keywords: str, location: str | None, page: int) -> str:
        params: dict[str, str | int] = {
            "siteKey": "AU-Main",
            "sourcesystem": "houston",
            "page": max(1, page),
        }
        if keywords:
            params["keywords"] = keywords
        if location:
            params["where"] = location

        response = self._client.get(API_URL, params=params, headers={"User-Agent": USER_AGENT})
        return response.text

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
