"""HTTP client for Greenhouse's public boards API.

``https://boards-api.greenhouse.io/v1/boards/{company}/jobs`` needs no
API key. We fetch one company board per request across the configured
list; a board that 404s or errors is skipped, never fatal (companies
change board tokens). ``content=true`` includes each posting's HTML
description so keyword matching and scoring have something to work with.
"""

from __future__ import annotations

import time
from typing import Any, Protocol

import httpx

from careeros_greenhouse_provider.companies import DEFAULT_COMPANY_BOARDS
from careeros_job_providers import JobProviderError

BOARDS_API = "https://boards-api.greenhouse.io/v1/boards"
USER_AGENT = "CareerOS/0.1 (+https://github.com/careeros; job-discovery bot)"


class GreenhouseTransport(Protocol):
    def fetch(self) -> list[dict[str, Any]]: ...


class HttpxGreenhouseTransport:
    """Real transport: one GET per configured company board."""

    def __init__(
        self,
        *,
        companies: tuple[str, ...] = DEFAULT_COMPANY_BOARDS,
        base_url: str = BOARDS_API,
        timeout: float = 15.0,
        per_board_delay_seconds: float = 0.3,
        client: httpx.Client | None = None,
    ) -> None:
        self._companies = companies
        self._base_url = base_url
        self._delay = per_board_delay_seconds
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout)

    def fetch(self) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        any_ok = False
        for company in self._companies:
            try:
                response = self._client.get(
                    f"{self._base_url}/{company}/jobs",
                    params={"content": "true"},
                    headers={"User-Agent": USER_AGENT},
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPError:
                continue  # a dead board must not sink the whole crawl
            any_ok = True
            for job in data.get("jobs", []):
                job["_company"] = company
                entries.append(job)
            time.sleep(self._delay)
        if not any_ok and self._companies:
            raise JobProviderError("Every Greenhouse board request failed")
        return entries

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
