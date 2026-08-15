"""RemoteOKProvider: the reference FIND_JOBS provider implementation."""

from __future__ import annotations

from careeros_job_providers import (
    HealthStatus,
    JobProvider,
    JobSearchQuery,
    JobSearchResult,
    ProviderHealth,
    filter_postings,
)
from careeros_remoteok_provider.client import HttpxRemoteOKTransport, RemoteOKTransport
from careeros_remoteok_provider.parser import is_job_entry, parse_job_entry


class RemoteOKProvider(JobProvider):
    """The reference job provider implementation, backed by RemoteOK's free public API."""

    def __init__(self, transport: RemoteOKTransport | None = None) -> None:
        self._transport = transport or HttpxRemoteOKTransport()

    @property
    def provider_id(self) -> str:
        return "remoteok"

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
