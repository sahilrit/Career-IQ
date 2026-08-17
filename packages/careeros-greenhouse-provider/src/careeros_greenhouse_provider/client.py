"""HTTP client for Greenhouse's public boards API.

``https://boards-api.greenhouse.io/v1/boards/{company}/jobs`` needs no
API key. We fetch one company board per request across the configured
list; a board that 404s or errors is skipped, never fatal (companies
change board tokens). ``content=true`` includes each posting's HTML
description so keyword matching and scoring have something to work with.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
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
        max_workers: int = 8,
        client: httpx.Client | None = None,
    ) -> None:
        self._companies = companies
        self._base_url = base_url
        self._max_workers = max_workers
        self._owns_client = client is None
        # httpx.Client is safe to share across threads (pooled connections).
        self._client = client or httpx.Client(timeout=timeout)

    def _fetch_board(self, company: str) -> list[dict[str, Any]] | None:
        """Return the board's jobs, or None if the request failed (a dead
        board must not sink the whole crawl)."""
        try:
            response = self._client.get(
                f"{self._base_url}/{company}/jobs",
                params={"content": "true"},
                headers={"User-Agent": USER_AGENT},
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError:
            return None
        jobs = data.get("jobs", [])
        for job in jobs:
            job["_company"] = company
        return jobs

    def fetch(self) -> list[dict[str, Any]]:
        if not self._companies:
            return []
        entries: list[dict[str, Any]] = []
        any_ok = False
        with ThreadPoolExecutor(max_workers=min(self._max_workers, len(self._companies))) as pool:
            for board_jobs in pool.map(self._fetch_board, self._companies):
                if board_jobs is None:
                    continue
                any_ok = True
                entries.extend(board_jobs)
        if not any_ok:
            raise JobProviderError("Every Greenhouse board request failed")
        return entries

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
