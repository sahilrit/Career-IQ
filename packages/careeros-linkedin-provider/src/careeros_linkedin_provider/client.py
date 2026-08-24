"""HTTP client for LinkedIn's public, logged-out job search.

LinkedIn renders its public job search from
``/jobs-guest/jobs/api/seeMoreJobPostings/search`` — the endpoint its own
infinite scroll calls. It returns a bare list of ``<li>`` job cards to any
client sending a browser User-Agent: no account, no cookie, no token.
Descriptions come from the equally public ``/jobs/view/{id}``.

Wrapped behind a ``LinkedInTransport`` protocol so the provider and parser
can be tested against captured HTML with no network access at all.

Note: LinkedIn's terms prohibit automated collection. This provider is
opt-in, off by default, and rate-limited — see ``README`` in
``docs/plans/job-ops-parity.md`` for the deployment guidance.
"""

from __future__ import annotations

import time
from typing import Protocol
from urllib.parse import urlencode

import httpx

from careeros_job_providers import JobProviderError

LINKEDIN_SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
LINKEDIN_JOB_VIEW_URL = "https://www.linkedin.com/jobs/view"

# A real desktop Chrome UA. The endpoint returns 400 to obviously-automated
# agents, and unlike most of our providers we cannot introduce ourselves.
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

#: LinkedIn serves 25 cards per request and ignores larger page sizes.
PAGE_SIZE = 25


class LinkedInTransport(Protocol):
    def fetch_search_page(self, *, keywords: str, location: str | None, start: int) -> str: ...

    def fetch_job_page(self, job_id: str) -> str: ...


class HttpxLinkedInTransport:
    """Real transport: paged GETs against the guest search endpoint.

    ``request_delay_seconds`` throttles us on purpose. The endpoint starts
    answering 429 well before it answers slowly, and a blocked IP costs far
    more than a slow search.
    """

    def __init__(
        self,
        *,
        search_url: str = LINKEDIN_SEARCH_URL,
        job_view_url: str = LINKEDIN_JOB_VIEW_URL,
        timeout: float = 15.0,
        request_delay_seconds: float = 1.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._search_url = search_url
        self._job_view_url = job_view_url
        self._request_delay_seconds = request_delay_seconds
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout, follow_redirects=True)

    def _get(self, url: str) -> str:
        try:
            response = self._client.get(url, headers={"User-Agent": USER_AGENT})
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise JobProviderError(f"LinkedIn request failed: {exc}") from exc
        if self._request_delay_seconds:
            time.sleep(self._request_delay_seconds)
        return response.text

    def fetch_search_page(self, *, keywords: str, location: str | None, start: int) -> str:
        params: dict[str, str | int] = {"keywords": keywords, "start": start}
        if location:
            params["location"] = location
        return self._get(f"{self._search_url}?{urlencode(params)}")

    def fetch_job_page(self, job_id: str) -> str:
        return self._get(f"{self._job_view_url}/{job_id}")

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
