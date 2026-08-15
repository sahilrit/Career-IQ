"""Normalizes raw Fiverr gig-card extractions into GigPosting records.

Note on Fiverr's model: unlike a bid-based freelance board (a buyer
posts a project, freelancers propose), a Fiverr "gig" is a service
listing created BY a seller. ``GigPosting.client_name`` is repurposed
here to hold that seller's name — the field name doesn't perfectly fit,
but this still proves the same ``FreelanceProvider`` interface works
across genuinely different marketplace shapes, which is this phase's
point.
"""

from __future__ import annotations

import re

from careeros_freelance_providers import Budget, GigPosting

PROVIDER_ID = "fiverr"
_PRICE_RE = re.compile(r"[\d,]+")


def _parse_price(raw: str | None) -> Budget | None:
    if not raw:
        return None
    match = _PRICE_RE.search(raw)
    if not match:
        return None
    amount = int(match.group().replace(",", ""))
    return Budget(min_amount=amount, max_amount=amount, currency="USD")


def _external_id_from_url(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1]


def parse_listing(entry: dict) -> GigPosting | None:
    """Returns ``None`` for a malformed entry rather than raising — one
    unexpected card on a search-results page shouldn't fail the whole
    search.
    """
    title = (entry.get("title") or "").strip()
    url = entry.get("url") or ""
    if not title or not url:
        return None
    return GigPosting(
        source_provider=PROVIDER_ID,
        external_id=_external_id_from_url(url),
        title=title,
        client_name=(entry.get("seller") or "Unknown seller").strip(),
        url=url,
        budget=_parse_price(entry.get("price")),
    )
