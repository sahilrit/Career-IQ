"""HTTP client for Adzuna's official jobs API.

Adzuna publishes a documented, keyed REST API covering 20+ countries. It is
the one high-volume aggregate source on our list that we are straightforwardly
entitled to use: register at https://developer.adzuna.com, set
``ADZUNA_APP_ID`` and ``ADZUNA_APP_KEY``, done. The free tier is generous
enough for normal use.

Without credentials the provider reports itself DOWN rather than raising, so
an install that has not registered simply searches its other sources.
"""

from __future__ import annotations

import os
from typing import Any, Protocol

import httpx

from careeros_job_providers import JobProviderError

ADZUNA_API_ROOT = "https://api.adzuna.com/v1/api/jobs"
ADZUNA_APP_ID_ENV_VAR = "ADZUNA_APP_ID"
ADZUNA_APP_KEY_ENV_VAR = "ADZUNA_APP_KEY"
USER_AGENT = "CareerOS/0.1 (+https://github.com/careeros; job-discovery bot)"

#: Adzuna caps a page at 50 results.
MAX_RESULTS_PER_PAGE = 50


def credentials() -> tuple[str, str] | None:
    app_id = (os.environ.get(ADZUNA_APP_ID_ENV_VAR) or "").strip()
    app_key = (os.environ.get(ADZUNA_APP_KEY_ENV_VAR) or "").strip()
    return (app_id, app_key) if app_id and app_key else None


class AdzunaTransport(Protocol):
    def search(
        self,
        *,
        country: str,
        page: int,
        what: str,
        where: str | None,
        results_per_page: int,
        max_days_old: int | None = None,
    ) -> list[dict[str, Any]]: ...


class HttpxAdzunaTransport:
    def __init__(
        self,
        *,
        api_root: str = ADZUNA_API_ROOT,
        timeout: float = 15.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._api_root = api_root
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout)

    def search(
        self,
        *,
        country: str,
        page: int,
        what: str,
        where: str | None,
        results_per_page: int,
        max_days_old: int | None = None,
    ) -> list[dict[str, Any]]:
        creds = credentials()
        if creds is None:
            raise JobProviderError(
                f"{ADZUNA_APP_ID_ENV_VAR} and {ADZUNA_APP_KEY_ENV_VAR} are not set"
            )
        app_id, app_key = creds

        params: dict[str, str | int] = {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": min(results_per_page, MAX_RESULTS_PER_PAGE),
            "content-type": "application/json",
        }
        if what:
            params["what"] = what
        if where:
            params["where"] = where
        if max_days_old:
            params["max_days_old"] = max_days_old

        # Adzuna pages are 1-indexed and live in the path, not the query.
        url = f"{self._api_root}/{country}/search/{max(1, page)}"
        try:
            response = self._client.get(url, params=params, headers={"User-Agent": USER_AGENT})
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise JobProviderError(f"Adzuna request failed: {exc}") from exc

        results = (payload or {}).get("results")
        if not isinstance(results, list):
            raise JobProviderError("Adzuna response contained no results list")
        return [result for result in results if isinstance(result, dict)]

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
