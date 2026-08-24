"""HTTP client for the golangjobs.tech board.

golangjobs.tech is a Supabase-backed site whose ``jobs`` table is served
through a public PostgREST endpoint with the site's anon key — the same
key the site ships to every browser. No account, no paid plan. We read
recent, non-archived rows and let the caller narrow by keyword.

The anon key is overridable via ``GOLANG_JOBS_SUPABASE_ANON_KEY`` in case
the site rotates it.
"""

from __future__ import annotations

import os
from typing import Any, Protocol

import httpx

from careeros_job_providers import JobProviderError

SUPABASE_URL = "https://mvjyjzestmcxxmmmakec.supabase.co"
JOBS_ENDPOINT = f"{SUPABASE_URL}/rest/v1/jobs"
_DEFAULT_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im12anlqemVzdG1jeHh"
    "tbW1ha2VjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM2NDMyNzksImV4cCI6MjA1OTIxOTI3OX0."
    "AEucvhTZofaPFnPmnCMM2ptuE3Iy06_uao4n-6AmEgM"
)
USER_AGENT = "CareerOS/0.1 (+https://github.com/careeros; job-discovery bot)"


def anon_key() -> str:
    return (os.environ.get("GOLANG_JOBS_SUPABASE_ANON_KEY") or "").strip() or _DEFAULT_ANON_KEY


class GolangJobsTransport(Protocol):
    def fetch(self, params: dict[str, str]) -> list[dict[str, Any]]: ...


class HttpxGolangJobsTransport:
    def __init__(
        self,
        *,
        endpoint: str = JOBS_ENDPOINT,
        timeout: float = 15.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._endpoint = endpoint
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout)

    def fetch(self, params: dict[str, str]) -> list[dict[str, Any]]:
        key = anon_key()
        try:
            response = self._client.get(
                self._endpoint,
                params=params,
                headers={
                    "apikey": key,
                    "Authorization": f"Bearer {key}",
                    "Accept": "application/json",
                    "User-Agent": USER_AGENT,
                },
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise JobProviderError(f"Golang Jobs request failed: {exc}") from exc
        if not isinstance(data, list):
            raise JobProviderError("Golang Jobs response was not a JSON array")
        return [row for row in data if isinstance(row, dict)]

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
