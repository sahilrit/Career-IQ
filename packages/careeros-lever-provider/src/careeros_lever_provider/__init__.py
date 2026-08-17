"""careeros_lever_provider: FIND_JOBS over company Lever boards
(free public v0 postings API, open jobs.lever.co application forms)."""

from __future__ import annotations

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

POSTINGS_API = "https://api.lever.co/v0/postings"
USER_AGENT = "CareerOS/0.1 (+https://github.com/careeros; job-discovery bot)"
PROVIDER_ID = "lever"

# Companies known to use Lever. Over-inclusion is safe: a board that errors
# or returns nothing is skipped. Pass your own tuple to override.
DEFAULT_COMPANY_BOARDS: tuple[str, ...] = (
    "spotify",
    "kpmg",
    "nielsen",
    "plaid",
    "voleon",
    "swordhealth",
    "matillion",
)

_TYPES = {
    "full-time": EmploymentType.FULL_TIME,
    "part-time": EmploymentType.PART_TIME,
    "contract": EmploymentType.CONTRACT,
    "intern": EmploymentType.INTERNSHIP,
    "internship": EmploymentType.INTERNSHIP,
}


class LeverTransport(Protocol):
    def fetch(self) -> list[dict[str, Any]]: ...


class HttpxLeverTransport:
    def __init__(
        self,
        *,
        companies: tuple[str, ...] = DEFAULT_COMPANY_BOARDS,
        base_url: str = POSTINGS_API,
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
                params={"mode": "json"},
                headers={"User-Agent": USER_AGENT},
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError:
            return None
        if not isinstance(data, list):
            return None
        for job in data:
            job["_company"] = company
        return data

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
            raise JobProviderError("Every Lever board request failed")
        return entries

    def close(self) -> None:
        if self._owns_client:
            self._client.close()


def is_job_entry(entry: dict[str, Any]) -> bool:
    return bool(entry.get("text")) and bool(entry.get("hostedUrl") or entry.get("applyUrl"))


def parse_job_entry(entry: dict[str, Any]) -> JobPosting:
    categories = entry.get("categories") or {}
    location = categories.get("location")
    commitment = (categories.get("commitment") or "").lower()
    workplace = (entry.get("workplaceType") or "").lower()
    remote = workplace == "remote" or bool(location and "remote" in location.lower())
    company = entry.get("_company") or ""
    tags = [
        str(value).lower()
        for value in (categories.get("department"), categories.get("team"))
        if value
    ]
    return JobPosting(
        source_provider=PROVIDER_ID,
        external_id=str(entry.get("id")),
        title=(entry.get("text") or "").strip(),
        company_name=str(company).replace("-", " ").title() if company else "",
        # applyUrl is the open jobs.lever.co hosted application form.
        url=entry.get("applyUrl") or entry.get("hostedUrl") or "",
        location=location,
        remote=remote,
        salary=None,
        employment_type=_TYPES.get(commitment, EmploymentType.FULL_TIME),
        description=entry.get("descriptionPlain") or "",
        tags=tags,
        posted_at=None,
    )


class LeverProvider(JobProvider):
    def __init__(self, transport: LeverTransport | None = None) -> None:
        self._transport = transport or HttpxLeverTransport()

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
    "POSTINGS_API",
    "HttpxLeverTransport",
    "LeverProvider",
    "LeverTransport",
    "is_job_entry",
    "parse_job_entry",
]
