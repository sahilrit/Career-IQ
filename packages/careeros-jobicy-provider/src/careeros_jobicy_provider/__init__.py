"""careeros_jobicy_provider: FIND_JOBS backed by Jobicy's free public API."""

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

JOBICY_API = "https://jobicy.com/api/v2/remote-jobs"
USER_AGENT = "CareerOS/0.1 (+https://github.com/careeros; job-discovery bot)"
PROVIDER_ID = "jobicy"
_TAG_RE = re.compile(r"<[^>]+>")

_TYPES = {
    "full-time": EmploymentType.FULL_TIME,
    "part-time": EmploymentType.PART_TIME,
    "contract": EmploymentType.CONTRACT,
    "freelance": EmploymentType.FREELANCE,
    "internship": EmploymentType.INTERNSHIP,
}


class JobicyTransport(Protocol):
    def fetch(self) -> list[dict[str, Any]]: ...


class HttpxJobicyTransport:
    def __init__(
        self,
        *,
        count: int = 100,
        base_url: str = JOBICY_API,
        timeout: float = 15.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._count = count
        self._base_url = base_url
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout)

    def fetch(self) -> list[dict[str, Any]]:
        try:
            response = self._client.get(
                self._base_url,
                params={"count": self._count},
                headers={"User-Agent": USER_AGENT},
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise JobProviderError(f"Jobicy request failed: {exc}") from exc
        if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
            raise JobProviderError("Jobicy response did not contain a 'jobs' array")
        return data["jobs"]

    def close(self) -> None:
        if self._owns_client:
            self._client.close()


def parse_job_entry(entry: dict[str, Any]) -> JobPosting:
    description = html.unescape(_TAG_RE.sub(" ", entry.get("jobDescription") or "")).strip()
    job_types = entry.get("jobType") or []
    if isinstance(job_types, str):
        job_types = [job_types]
    employment = (
        _TYPES.get(job_types[0].lower(), EmploymentType.FULL_TIME)
        if job_types
        else (EmploymentType.FULL_TIME)
    )
    industry = entry.get("jobIndustry") or []
    if isinstance(industry, str):
        industry = [industry]
    return JobPosting(
        source_provider=PROVIDER_ID,
        external_id=str(entry.get("id")),
        title=(entry.get("jobTitle") or "").strip(),
        company_name=(entry.get("companyName") or "").strip(),
        url=entry.get("url") or "",
        location=entry.get("jobGeo") or None,
        remote=True,
        salary=None,
        employment_type=employment,
        description=description or (entry.get("jobExcerpt") or ""),
        tags=[str(item).lower() for item in industry],
        posted_at=None,
    )


class JobicyProvider(JobProvider):
    def __init__(self, transport: JobicyTransport | None = None) -> None:
        self._transport = transport or HttpxJobicyTransport()

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
    "JOBICY_API",
    "HttpxJobicyTransport",
    "JobicyProvider",
    "JobicyTransport",
    "parse_job_entry",
]
