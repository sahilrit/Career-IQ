"""careeros_workingnomads_provider: FIND_JOBS backed by Working Nomads'
free public jobs feed."""

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

WORKINGNOMADS_API = "https://www.workingnomads.com/api/exposed_jobs/"
USER_AGENT = "CareerOS/0.1 (+https://github.com/careeros; job-discovery bot)"
PROVIDER_ID = "workingnomads"
_TAG_RE = re.compile(r"<[^>]+>")


class WorkingNomadsTransport(Protocol):
    def fetch(self) -> list[dict[str, Any]]: ...


class HttpxWorkingNomadsTransport:
    def __init__(
        self,
        *,
        base_url: str = WORKINGNOMADS_API,
        timeout: float = 15.0,
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
            raise JobProviderError(f"Working Nomads request failed: {exc}") from exc
        if not isinstance(data, list):
            raise JobProviderError("Working Nomads response was not a list")
        return data

    def close(self) -> None:
        if self._owns_client:
            self._client.close()


def parse_job_entry(entry: dict[str, Any]) -> JobPosting:
    description = html.unescape(_TAG_RE.sub(" ", entry.get("description") or "")).strip()
    tags_raw = entry.get("tags") or ""
    tags = [t.strip().lower() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
    category = entry.get("category_name")
    if category:
        tags.append(str(category).lower())
    return JobPosting(
        source_provider=PROVIDER_ID,
        external_id=entry.get("url") or entry.get("title") or "",
        title=(entry.get("title") or "").strip(),
        company_name=(entry.get("company_name") or "").strip(),
        url=entry.get("url") or "",
        location=entry.get("location") or None,
        remote=True,
        salary=None,
        employment_type=EmploymentType.FULL_TIME,
        description=description,
        tags=tags,
        posted_at=None,
    )


class WorkingNomadsProvider(JobProvider):
    def __init__(self, transport: WorkingNomadsTransport | None = None) -> None:
        self._transport = transport or HttpxWorkingNomadsTransport()

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
    "WORKINGNOMADS_API",
    "HttpxWorkingNomadsTransport",
    "WorkingNomadsProvider",
    "WorkingNomadsTransport",
    "parse_job_entry",
]
