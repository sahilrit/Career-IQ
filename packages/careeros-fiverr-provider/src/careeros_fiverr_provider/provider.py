"""FiverrProvider: proves the freelance provider architecture (Phase 18)
works across marketplaces, browser-driven since Fiverr has no free
public API.
"""

from __future__ import annotations

from careeros_fiverr_provider.parser import parse_listing
from careeros_fiverr_provider.transport import FiverrTransport
from careeros_freelance_providers import (
    FreelanceProvider,
    GigSearchQuery,
    GigSearchResult,
    HealthStatus,
    ProviderHealth,
    filter_postings,
)


class FiverrProvider(FreelanceProvider):
    """A transport must be supplied (unlike RemoteOKProvider's default HTTP
    client, a Fiverr transport needs an already-open browser session, which
    this provider deliberately does not launch on the caller's behalf).
    """

    def __init__(self, transport: FiverrTransport) -> None:
        self._transport = transport

    @property
    def provider_id(self) -> str:
        return "fiverr"

    def search(self, query: GigSearchQuery) -> GigSearchResult:
        raw_entries = self._transport.fetch_listings(query)
        postings = [posting for entry in raw_entries if (posting := parse_listing(entry))]
        filtered = filter_postings(postings, query)
        return GigSearchResult(postings=filtered[: query.limit])

    def health_check(self) -> ProviderHealth:
        try:
            self._transport.fetch_listings(GigSearchQuery(limit=1))
        except Exception as exc:
            return ProviderHealth(status=HealthStatus.DOWN, detail=str(exc))
        return ProviderHealth(status=HealthStatus.HEALTHY)
