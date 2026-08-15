"""Company discovery: pluggable, mirroring careeros_job_providers'
JobProvider pattern (Phase 6).

Unlike RemoteOK (Phase 7), there is no free public API that lists
"companies that might need freelance help" — real discovery sources
(Shopify's app-store category pages, a Meta Ad Library search, a
LinkedIn Sales Navigator export) each need their own provider, built
the same way careeros-fiverr-provider (Phase 19) was: against real,
verified selectors for that specific source. ``ManualCompanyDiscoveryProvider``
is the zero-cost reference implementation every install has by
default — it discovers from a list the user already supplies (e.g. an
exported CSV of leads), rather than fabricating or guessing scraper
selectors for a site nobody has verified.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from careeros_client_acquisition.company import Company


class CompanyDiscoveryQuery(BaseModel):
    industry: str | None = None
    keywords: list[str] = Field(default_factory=list)


class CompanyDiscoveryProvider(Protocol):
    def discover(self, query: CompanyDiscoveryQuery) -> list[Company]: ...


class ManualCompanyDiscoveryProvider:
    """Discovers from a fixed, user-supplied list of companies."""

    def __init__(self, companies: list[Company]) -> None:
        self._companies = list(companies)

    def discover(self, query: CompanyDiscoveryQuery) -> list[Company]:
        results = list(self._companies)
        if query.industry:
            results = [c for c in results if c.industry == query.industry]
        if query.keywords:
            keywords_lower = [k.lower() for k in query.keywords]
            results = [
                c
                for c in results
                if any(k in c.name.lower() or k in c.notes.lower() for k in keywords_lower)
            ]
        return results
