"""Fiverr transport: browser-driven, since Fiverr has no free public API
for gig listings. Uses the ``BrowserSession`` abstraction (Phase 13)
rather than a bespoke scraper — the same pattern any future
browser-only provider (LinkedIn, Indeed, ...) will follow.
"""

from __future__ import annotations

from typing import Protocol
from urllib.parse import quote

from careeros_browser import BrowserSession
from careeros_fiverr_provider.selectors import FiverrSelectors
from careeros_freelance_providers import GigSearchQuery

FIVERR_SEARCH_URL = "https://www.fiverr.com/search/gigs?query={query}"


class FiverrTransport(Protocol):
    def fetch_listings(self, query: GigSearchQuery) -> list[dict]: ...


class BrowserFiverrTransport:
    """Real transport: navigates a live ``BrowserSession`` to Fiverr's
    public search results and extracts each gig card via ``query_all``.

    Requires a human-reviewed ``FiverrSelectors`` matching Fiverr's
    current markup — see that class's docstring before using this
    against the live site.
    """

    def __init__(
        self, session: BrowserSession, *, selectors: FiverrSelectors | None = None
    ) -> None:
        self._session = session
        self._selectors = selectors or FiverrSelectors()

    def fetch_listings(self, query: GigSearchQuery) -> list[dict]:
        search_term = " ".join(query.keywords) or " ".join(query.skills) or ""
        url = FIVERR_SEARCH_URL.format(query=quote(search_term))
        self._session.goto(url)
        return self._session.query_all(
            self._selectors.listing_selector,
            extract={
                "title": self._selectors.title_selector,
                "seller": self._selectors.seller_selector,
                "price": self._selectors.price_selector,
                "url": self._selectors.url_selector,
            },
        )
