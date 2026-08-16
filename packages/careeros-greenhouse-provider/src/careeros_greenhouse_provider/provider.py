"""GreenhouseProvider: FIND_JOBS across many company Greenhouse boards.

The postings it returns link to open, hosted application forms — the
one source in the pool the autopilot can genuinely submit to without a
login wall or captcha.
"""

from __future__ import annotations

from careeros_greenhouse_provider.client import GreenhouseTransport, HttpxGreenhouseTransport
from careeros_greenhouse_provider.parser import is_job_entry, parse_job_entry
from careeros_job_providers import (
    HealthStatus,
    JobProvider,
    JobSearchQuery,
    JobSearchResult,
    ProviderHealth,
    filter_postings,
)


class GreenhouseProvider(JobProvider):
    def __init__(self, transport: GreenhouseTransport | None = None) -> None:
        self._transport = transport or HttpxGreenhouseTransport()

    @property
    def provider_id(self) -> str:
        return "greenhouse"

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
