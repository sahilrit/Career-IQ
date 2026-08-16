"""careeros_themuse_provider: FIND_JOBS from The Muse's free public jobs
API. Aggregator volume (discovery-only — postings link to Muse landing
pages), filterable by category and paged."""

from __future__ import annotations

import html
import re
from typing import Any, Protocol

import httpx

from careeros_job_providers import (
    EmploymentType,
    HealthStatus,
    JobPosting,
    JobProvider,
    JobProviderError,
    JobSearchQuery,
    JobSearchResult,
    ProviderHealth,
    filter_postings,
)

MUSE_API = "https://www.themuse.com/api/public/jobs"
USER_AGENT = "CareerOS/0.1 (+https://github.com/careeros; job-discovery bot)"
PROVIDER_ID = "themuse"
_TAG_RE = re.compile(r"<[^>]+>")

DEFAULT_CATEGORIES: tuple[str, ...] = (
    "Marketing",
    "Sales",
    "Business & Strategy",
    "Creative & Design",
)


class TheMuseTransport(Protocol):
    def fetch(self) -> list[dict[str, Any]]: ...


class HttpxTheMuseTransport:
    def __init__(
        self,
        *,
        categories: tuple[str, ...] = DEFAULT_CATEGORIES,
        pages: int = 3,
        base_url: str = MUSE_API,
        timeout: float = 15.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._categories = categories
        self._pages = pages
        self._base_url = base_url
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout)

    def fetch(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        any_ok = False
        for page in range(self._pages):
            params = [("page", page)]
            params += [("category", category) for category in self._categories]
            try:
                response = self._client.get(
                    self._base_url, params=params, headers={"User-Agent": USER_AGENT}
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPError:
                continue
            any_ok = True
            page_results = data.get("results", []) if isinstance(data, dict) else []
            results.extend(page_results)
            if not page_results:
                break
        if not any_ok:
            raise JobProviderError("Every The Muse request failed")
        return results


def parse_job_entry(entry: dict[str, Any]) -> JobPosting:
    locations = [loc.get("name", "") for loc in entry.get("locations") or []]
    location = ", ".join(filter(None, locations)) or None
    remote = any("remote" in loc.lower() or "flexible" in loc.lower() for loc in locations)
    company = (entry.get("company") or {}).get("name") or ""
    landing = (entry.get("refs") or {}).get("landing_page") or ""
    levels = [lvl.get("name", "") for lvl in entry.get("levels") or []]
    categories = [cat.get("name", "") for cat in entry.get("categories") or []]
    return JobPosting(
        source_provider=PROVIDER_ID,
        external_id=str(entry.get("id")),
        title=(entry.get("name") or "").strip(),
        company_name=str(company).strip(),
        url=landing,
        location=location,
        remote=remote,
        salary=None,
        employment_type=EmploymentType.FULL_TIME,
        description=html.unescape(_TAG_RE.sub(" ", entry.get("contents") or "")).strip(),
        tags=[t.lower() for t in categories + levels if t],
        posted_at=None,
    )


class TheMuseProvider(JobProvider):
    def __init__(self, transport: TheMuseTransport | None = None) -> None:
        self._transport = transport or HttpxTheMuseTransport()

    @property
    def provider_id(self) -> str:
        return PROVIDER_ID

    def search(self, query: JobSearchQuery) -> JobSearchResult:
        postings = [parse_job_entry(entry) for entry in self._transport.fetch()]
        return JobSearchResult(postings=filter_postings(postings, query)[: query.limit])

    def health_check(self) -> ProviderHealth:
        try:
            self._transport.fetch()
        except Exception as exc:
            return ProviderHealth(status=HealthStatus.DOWN, detail=str(exc))
        return ProviderHealth(status=HealthStatus.HEALTHY)


__all__ = [
    "DEFAULT_CATEGORIES",
    "MUSE_API",
    "HttpxTheMuseTransport",
    "TheMuseProvider",
    "TheMuseTransport",
    "parse_job_entry",
]
