"""careeros_ashby_provider: FIND_JOBS over company Ashby boards
(free public posting API, open jobs.ashbyhq.com application forms)."""

from __future__ import annotations

import html
import re
from concurrent.futures import ThreadPoolExecutor
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

POSTING_API = "https://api.ashbyhq.com/posting-api/job-board"
USER_AGENT = "CareerOS/0.1 (+https://github.com/careeros; job-discovery bot)"
PROVIDER_ID = "ashby"
_TAG_RE = re.compile(r"<[^>]+>")

DEFAULT_COMPANY_BOARDS: tuple[str, ...] = (
    "ramp",
    "notion",
    "linear",
    "posthog",
    "cohere",
    "replit",
    "hex",
    "watershed",
    "runway",
    "openai",
    "vanta",
    "eightsleep",
    "ashby",
    "found",
    "airbyte",
    "perplexity",
    "suno",
    "elevenlabs",
    "harvey",
    "crusoe",
    "cursor",
    "modal",
    "pika",
    "sierra",
    "warp",
    "writer",
)

_TYPES = {
    "fulltime": EmploymentType.FULL_TIME,
    "parttime": EmploymentType.PART_TIME,
    "contract": EmploymentType.CONTRACT,
    "intern": EmploymentType.INTERNSHIP,
}


class AshbyTransport(Protocol):
    def fetch(self) -> list[dict[str, Any]]: ...


class HttpxAshbyTransport:
    def __init__(
        self,
        *,
        companies: tuple[str, ...] = DEFAULT_COMPANY_BOARDS,
        base_url: str = POSTING_API,
        timeout: float = 15.0,
        max_workers: int = 8,
        client: httpx.Client | None = None,
    ) -> None:
        self._companies = companies
        self._base_url = base_url
        self._max_workers = max_workers
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout)

    def _fetch_board(self, company: str) -> list[dict[str, Any]] | None:
        try:
            response = self._client.get(
                f"{self._base_url}/{company}",
                params={"includeCompensation": "false"},
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
            raise JobProviderError("Every Ashby board request failed")
        return entries

    def close(self) -> None:
        if self._owns_client:
            self._client.close()


def is_job_entry(entry: dict[str, Any]) -> bool:
    return bool(entry.get("title")) and bool(entry.get("jobUrl") or entry.get("applyUrl"))


def parse_job_entry(entry: dict[str, Any]) -> JobPosting:
    description = entry.get("descriptionPlain") or html.unescape(
        _TAG_RE.sub(" ", entry.get("descriptionHtml") or "")
    )
    employment_raw = re.sub(r"[^a-z]", "", (entry.get("employmentType") or "").lower())
    department = entry.get("department") or ""
    team = entry.get("team") or ""
    company = entry.get("_company") or ""
    return JobPosting(
        source_provider=PROVIDER_ID,
        external_id=str(entry.get("id")),
        title=(entry.get("title") or "").strip(),
        company_name=str(company).replace("-", " ").title() if company else "",
        # applyUrl/jobUrl is the open jobs.ashbyhq.com hosted application form.
        url=entry.get("applyUrl") or entry.get("jobUrl") or "",
        location=entry.get("location") or None,
        remote=bool(entry.get("isRemote")),
        salary=None,
        employment_type=_TYPES.get(employment_raw, EmploymentType.FULL_TIME),
        description=description.strip(),
        tags=[t.lower() for t in (department, team) if t],
        posted_at=None,
    )


class AshbyProvider(JobProvider):
    def __init__(self, transport: AshbyTransport | None = None) -> None:
        self._transport = transport or HttpxAshbyTransport()

    @property
    def provider_id(self) -> str:
        return PROVIDER_ID

    def search(self, query: JobSearchQuery) -> JobSearchResult:
        postings = [
            parse_job_entry(entry) for entry in self._transport.fetch() if is_job_entry(entry)
        ]
        return JobSearchResult(postings=filter_postings(postings, query)[: query.limit])

    def health_check(self) -> ProviderHealth:
        # Optimistic — see the note in GreenhouseProvider.health_check.
        return ProviderHealth(status=HealthStatus.HEALTHY)


__all__ = [
    "DEFAULT_COMPANY_BOARDS",
    "POSTING_API",
    "AshbyProvider",
    "AshbyTransport",
    "HttpxAshbyTransport",
    "is_job_entry",
    "parse_job_entry",
]
