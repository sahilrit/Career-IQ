"""HTTP client for Hiring Cafe's search pages."""

from __future__ import annotations

import json
from typing import Any, Protocol

import httpx

from careeros_job_providers import JobProviderError

HIRINGCAFE_BASE_URL = "https://hiring.cafe/"
USER_AGENT = "CareerOS/0.1 (+https://github.com/careeros; job-discovery bot)"


class HiringCafeTransport(Protocol):
    def fetch_search_page(self, *, search_state: dict[str, Any], page: int) -> str: ...


class HttpxHiringCafeTransport:
    """Real transport: one GET per results page.

    ``follow_redirects`` matters — hiring.cafe 308s to hiringcafe.com, and
    without it every request comes back as a 15-byte redirect body.
    """

    def __init__(
        self,
        *,
        base_url: str = HIRINGCAFE_BASE_URL,
        timeout: float = 20.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout, follow_redirects=True)

    def fetch_search_page(self, *, search_state: dict[str, Any], page: int) -> str:
        params: dict[str, str] = {"searchState": json.dumps(search_state)}
        if page > 0:
            params["page"] = str(page)
        try:
            response = self._client.get(
                self._base_url,
                params=params,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise JobProviderError(f"Hiring Cafe request failed: {exc}") from exc
        return response.text

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
