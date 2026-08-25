"""SeekProvider: FIND_JOBS over Seek via its own public search API."""

from __future__ import annotations

from careeros_common import get_logger
from careeros_job_providers import (
    HealthStatus,
    JobPosting,
    JobProvider,
    JobSearchQuery,
    JobSearchResult,
    ProviderHealth,
)
from careeros_seek_provider.client import HttpxSeekTransport, SeekTransport
from careeros_seek_provider.parser import (
    PROVIDER_ID,
    is_job_entry,
    parse_job_entry,
    parse_search_response,
)

logger = get_logger(__name__)

DEFAULT_MAX_PAGES = 4
PAGE_SIZE = 20


class SeekProvider(JobProvider):
    def __init__(
        self, transport: SeekTransport | None = None, *, max_pages: int = DEFAULT_MAX_PAGES
    ) -> None:
        self._transport = transport or HttpxSeekTransport()
        self._max_pages = max(1, max_pages)

    @property
    def provider_id(self) -> str:
        return PROVIDER_ID

    def search(self, query: JobSearchQuery) -> JobSearchResult:
        keywords = " ".join(k.strip() for k in query.keywords if k.strip())
        location = next((loc.strip() for loc in query.locations if loc.strip()), None)

        postings: list[JobPosting] = []
        seen: set[str] = set()
        page = 1

        while page <= self._max_pages and len(postings) < query.limit:
            body = self._transport.search(keywords=keywords, location=location, page=page)
            parsed = parse_search_response(body)
            rows = parsed["jobs"]
            if not rows:
                break

            for row in rows:
                if not is_job_entry(row):
                    continue
                posting = parse_job_entry(row)
                if posting.external_id in seen:
                    continue
                seen.add(posting.external_id)
                postings.append(posting)

            if len(rows) < PAGE_SIZE:
                break
            page += 1

        return JobSearchResult(postings=postings[: query.limit])

    def health_check(self) -> ProviderHealth:
        # Optimistic, matching other keyless providers (HiringCafe): a real
        # check would double the cost of every search, since the registry
        # health-checks every provider before every search.
        return ProviderHealth(status=HealthStatus.HEALTHY)
