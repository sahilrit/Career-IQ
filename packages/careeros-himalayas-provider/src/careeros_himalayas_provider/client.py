"""Thin HTTP client for Himalayas' public remote-jobs API.

``https://himalayas.app/jobs/api`` requires no API key and no paid
plan — a plain public JSON endpoint returning ``{"jobs": [...],
"totalCount": N, ...}`` with ``limit``/``offset`` paging. The feed is
recency-ordered and 100k+ deep; we fetch a few pages of the most
recent postings rather than the whole catalog.
"""

from __future__ import annotations

import time
from typing import Any, Protocol

import httpx

from careeros_job_providers import JobProviderError

HIMALAYAS_API_URL = "https://himalayas.app/jobs/api"
USER_AGENT = "CareerOS/0.1 (+https://github.com/careeros; job-discovery bot)"

_REQUESTED_PAGE_SIZE = 100  # the API serves fewer (currently 20); we page by what it returns
_DEFAULT_MAX_ENTRIES = 400


class HimalayasTransport(Protocol):
    def fetch(self) -> list[dict[str, Any]]: ...


class HttpxHimalayasTransport:
    """Real transport: paged GETs against Himalayas' public API.

    The API ignores large ``limit`` values (it currently serves 20 per
    call), so paging advances by however many entries each response
    actually contains, until ``max_entries`` or the feed end.

    Accepts an optional pre-built ``httpx.Client`` so tests can inject one
    backed by ``httpx.MockTransport`` instead of touching the network.
    """

    def __init__(
        self,
        *,
        base_url: str = HIMALAYAS_API_URL,
        max_entries: int = _DEFAULT_MAX_ENTRIES,
        timeout: float = 15.0,
        page_delay_seconds: float = 0.5,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url
        self._max_entries = max_entries
        self._page_delay_seconds = page_delay_seconds
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout)

    def fetch(self) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        offset = 0
        while len(entries) < self._max_entries:
            try:
                response = self._client.get(
                    self._base_url,
                    params={"limit": _REQUESTED_PAGE_SIZE, "offset": offset},
                    headers={"User-Agent": USER_AGENT},
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPError as exc:
                # A mid-crawl failure (e.g. 429 rate limit) shouldn't discard
                # the pages already fetched — partial coverage beats none.
                if entries:
                    break
                raise JobProviderError(f"Himalayas request failed: {exc}") from exc
            if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
                raise JobProviderError("Himalayas response did not contain a 'jobs' array")
            page_jobs = data["jobs"]
            if not page_jobs:
                break
            entries.extend(page_jobs)
            offset += len(page_jobs)
            time.sleep(self._page_delay_seconds)
        return entries[: self._max_entries]

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
