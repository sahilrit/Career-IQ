"""Shared fixtures for ZipRecruiter provider tests. No real network or
browser.

The ``itemListElement`` shape mirrors the JSON-LD ``ItemList`` structured
data ZipRecruiter's own search-results page embeds in a
``<script type="application/ld+json">`` block — verified against a live
page (2026-08-26, after a real Camoufox session passed the site's
Cloudflare challenge).
"""

from __future__ import annotations

from typing import Any

import pytest

ITEM_FULL: dict[str, Any] = {
    "@type": "ListItem",
    "position": "1",
    "name": "Manager, Business Development - Green Chef",
    "url": "https://www.ziprecruiter.com/c/HelloFresh/Job/Manager,-Business-Development-Green-Chef/-in-New-York,NY?jid=543ce44ea13a0486",
}

ITEM_MULTIWORD_COMPANY: dict[str, Any] = {
    "@type": "ListItem",
    "position": "2",
    "name": "Graphic Designer",
    "url": "https://www.ziprecruiter.com/c/AMERICAN-MANAGEMENT-ASSOC./Job/Graphic-Designer/-in-Manhattan,NY?jid=7a9e2948525e8e46",
}

ITEM_UNUSABLE: dict[str, Any] = {"@type": "ListItem", "position": "3"}

LISTING_HTML = """
<html><body>
<script type="application/ld+json">
{"@context": "https://schema.org", "@type": "ItemList", "numberOfItems": 2,
 "itemListElement": [
   {"@type": "ListItem", "position": "1", "name": "A",
    "url": "https://www.ziprecruiter.com/c/Acme/Job/A/-in-Austin,TX?jid=aaa111"},
   {"@type": "ListItem", "position": "2", "name": "B",
    "url": "https://www.ziprecruiter.com/c/Widget-Co/Job/B/-in-Denver,CO?jid=bbb222"}
 ]}
</script>
</body></html>
"""


@pytest.fixture
def item_full() -> dict[str, Any]:
    return ITEM_FULL


@pytest.fixture
def item_multiword_company() -> dict[str, Any]:
    return ITEM_MULTIWORD_COMPANY


@pytest.fixture
def item_unusable() -> dict[str, Any]:
    return ITEM_UNUSABLE


@pytest.fixture
def listing_html() -> str:
    return LISTING_HTML
