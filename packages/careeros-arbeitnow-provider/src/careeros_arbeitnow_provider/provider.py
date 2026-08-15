"""ArbeitnowProvider: a second FIND_JOBS provider, proving the SDK
generalizes beyond RemoteOK the same way Phase 19's Fiverr provider
proved FIND_GIGS generalizes beyond Freelancer.
"""

from __future__ import annotations

from careeros_arbeitnow_provider.client import ArbeitnowTransport, HttpxArbeitnowTransport
from careeros_arbeitnow_provider.parser import parse_job_entry
from careeros_job_providers import (
    HealthStatus,
    JobProvider,
    JobSearchQuery,
    JobSearchResult,
    ProviderHealth,
    filter_postings,
)


class ArbeitnowProvider(JobProvider):
    """A FIND_JOBS provider backed by Arbeitnow's free public job board API."""

    def __init__(self, transport: ArbeitnowTransport | None = None) -> None:
        self._transport = transport or HttpxArbeitnowTransport()

    @property
    def provider_id(self) -> str:
        return "arbeitnow"

    def search(self, query: JobSearchQuery) -> JobSearchResult:
        raw_entries = self._transport.fetch()
        postings = [parse_job_entry(entry) for entry in raw_entries]
        filtered = filter_postings(postings, query)
        return JobSearchResult(postings=filtered[: query.limit])

    def health_check(self) -> ProviderHealth:
        try:
            self._transport.fetch()
        except Exception as exc:
            return ProviderHealth(status=HealthStatus.DOWN, detail=str(exc))
        return ProviderHealth(status=HealthStatus.HEALTHY)
