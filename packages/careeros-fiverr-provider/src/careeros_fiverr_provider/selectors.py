"""CSS selectors for Fiverr's public gig search results page.

Fiverr's markup changes over time and is not publicly documented, so
these defaults are a **starting point, not a guarantee** — verify them
against the live site (e.g. via browser devtools) before relying on this
provider in production, and update them here or via the
``FiverrProvider``/``BrowserFiverrTransport`` constructor if Fiverr's
markup has moved on. This is exactly why the selectors are a plain,
overridable dataclass rather than hardcoded strings inside the parser.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FiverrSelectors:
    listing_selector: str = "[data-testid='gig-card-layout']"
    title_selector: str = "[data-testid='gig-card-title']"
    seller_selector: str = "[data-testid='seller-name']"
    price_selector: str = "[data-testid='gig-card-price']"
    url_selector: str = "a@href"
