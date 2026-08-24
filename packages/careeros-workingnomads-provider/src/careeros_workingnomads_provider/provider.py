"""WorkingNomadsProvider: FIND_JOBS over Working Nomads' search backend."""

from __future__ import annotations

from careeros_job_providers import (
    HealthStatus,
    JobProvider,
    JobSearchQuery,
    JobSearchResult,
    ProviderHealth,
    filter_postings,
)
from careeros_workingnomads_provider.client import (
    HttpxWorkingNomadsTransport,
    WorkingNomadsTransport,
)
from careeros_workingnomads_provider.parser import (
    PROVIDER_ID,
    is_job_entry,
    parse_job_entry,
)


class WorkingNomadsProvider(JobProvider):
    def __init__(self, transport: WorkingNomadsTransport | None = None) -> None:
        self._transport = transport or HttpxWorkingNomadsTransport()

    @property
    def provider_id(self) -> str:
        return PROVIDER_ID

    def search(self, query: JobSearchQuery) -> JobSearchResult:
        docs = self._transport.search(keywords=list(query.keywords), size=query.limit)
        postings = [parse_job_entry(doc) for doc in docs if is_job_entry(doc)]
        # The backend scored these against full job text. Our local haystack is
        # narrower, so re-checking keywords here would discard real matches.
        # Everything else — salary floor, employment type — it can't do for us.
        filtered = filter_postings(postings, query, applied_server_side={"keywords"})
        return JobSearchResult(postings=filtered[: query.limit])

    def health_check(self) -> ProviderHealth:
        """One document is enough to know the index is answering, and this
        runs before every search."""
        try:
            self._transport.search(keywords=[], size=1)
        except Exception as exc:
            return ProviderHealth(status=HealthStatus.DOWN, detail=str(exc))
        return ProviderHealth(status=HealthStatus.HEALTHY)
