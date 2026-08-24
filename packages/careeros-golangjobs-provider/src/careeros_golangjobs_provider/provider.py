"""GolangJobsProvider: FIND_JOBS over the golangjobs.tech board."""

from __future__ import annotations

from careeros_golangjobs_provider.client import (
    GolangJobsTransport,
    HttpxGolangJobsTransport,
)
from careeros_golangjobs_provider.parser import PROVIDER_ID, is_job_entry, parse_job_entry
from careeros_job_providers import (
    HealthStatus,
    JobProvider,
    JobSearchQuery,
    JobSearchResult,
    ProviderHealth,
    filter_postings,
)

# The board is Go-only and modest in size, so a single recent, non-archived
# page is plenty; keyword narrowing happens locally, like the other
# feed-shaped providers.
_FETCH_LIMIT = 200


class GolangJobsProvider(JobProvider):
    def __init__(self, transport: GolangJobsTransport | None = None) -> None:
        self._transport = transport or HttpxGolangJobsTransport()

    @property
    def provider_id(self) -> str:
        return PROVIDER_ID

    def _params(self, limit: int) -> dict[str, str]:
        return {
            "select": "*",
            "is_archived": "eq.false",
            "order": "posted_at.desc",
            "limit": str(limit),
        }

    def search(self, query: JobSearchQuery) -> JobSearchResult:
        rows = self._transport.fetch(self._params(_FETCH_LIMIT))
        postings = [parse_job_entry(row) for row in rows if is_job_entry(row)]
        # Archived rows are excluded server-side; keyword/salary/etc. narrowing
        # is local, matching the reference feed-style providers.
        filtered = filter_postings(postings, query)
        return JobSearchResult(postings=filtered[: query.limit])

    def health_check(self) -> ProviderHealth:
        try:
            self._transport.fetch({"select": "id", "limit": "1"})
        except Exception as exc:
            return ProviderHealth(status=HealthStatus.DOWN, detail=str(exc))
        return ProviderHealth(status=HealthStatus.HEALTHY)
