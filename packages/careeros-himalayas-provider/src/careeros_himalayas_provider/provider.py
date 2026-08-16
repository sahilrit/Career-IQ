"""HimalayasProvider: a third FIND_JOBS provider, adding real volume
(100k+ remote postings, including marketing/sales/ops roles the
tech-centric boards lack)."""

from __future__ import annotations

from careeros_himalayas_provider.client import HimalayasTransport, HttpxHimalayasTransport
from careeros_himalayas_provider.parser import is_job_entry, parse_job_entry
from careeros_job_providers import (
    HealthStatus,
    JobProvider,
    JobSearchQuery,
    JobSearchResult,
    ProviderHealth,
    filter_postings,
)


class HimalayasProvider(JobProvider):
    """A FIND_JOBS provider backed by Himalayas' free public remote-jobs API."""

    def __init__(self, transport: HimalayasTransport | None = None) -> None:
        self._transport = transport or HttpxHimalayasTransport()

    @property
    def provider_id(self) -> str:
        return "himalayas"

    def search(self, query: JobSearchQuery) -> JobSearchResult:
        raw_entries = self._transport.fetch()
        postings = [parse_job_entry(entry) for entry in raw_entries if is_job_entry(entry)]
        filtered = filter_postings(postings, query)
        return JobSearchResult(postings=filtered[: query.limit])

    def health_check(self) -> ProviderHealth:
        try:
            self._transport.fetch()
        except Exception as exc:
            return ProviderHealth(status=HealthStatus.DOWN, detail=str(exc))
        return ProviderHealth(status=HealthStatus.HEALTHY)
