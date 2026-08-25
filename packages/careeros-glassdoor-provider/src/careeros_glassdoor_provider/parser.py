"""Glassdoor: URL building and job-card parsing.

Field anchors (``data-test="job-title"``, ``data-test="emp-location"``,
``data-test="detailSalary"``, ``data-test="descSnippet"``,
``EmployerProfile_compactEmployerName__...``) are grounded in a real
search-results card captured live (2026-08-26) after a real anti-detect
browser session passed the site's bot wall — see ``tests/conftest.py``.

Everything here is pure — no browser, no network. The Camoufox session
that produces real page HTML lives in ``provider.py``.
"""

from __future__ import annotations

import html as html_module
import re
from urllib.parse import urlencode

from careeros_job_providers import JobPosting, Salary

PROVIDER_ID = "glassdoor"
BASE_URL = "https://www.glassdoor.com"
SEARCH_PATH = "/Job/jobs.htm"

CARD_SELECTOR = '[data-test="job-card-wrapper"]'

_REMOTE_TOKENS = ("remote",)

_TITLE_ID_RE = re.compile(r'id="job-title-(\d+)"')
_TITLE_TEXT_RE = re.compile(r'data-test="job-title"[^>]*>([^<]*)<')
_TITLE_HREF_RE = re.compile(r'data-test="job-title"[^>]*href="([^"]*)"')
_COMPANY_RE = re.compile(r'EmployerProfile_compactEmployerName__[^"]*">([^<]*)</span>')
_LOCATION_RE = re.compile(r'data-test="emp-location"[^>]*>([^<]*)<')
_SALARY_RE = re.compile(r'data-test="detailSalary"[^>]*>(.*?)</div>', re.DOTALL)
_DESC_RE = re.compile(r'data-test="descSnippet"[^>]*>\s*<div>([^<]*)</div>', re.DOTALL)

# Currency symbol -> ISO code, and the abbreviation multiplier Glassdoor
# uses per region (K = thousand everywhere; L = lakh, India-specific).
_CURRENCY_CODES = {"$": "USD", "₹": "INR", "£": "GBP", "€": "EUR"}
_SALARY_AMOUNT_RE = re.compile(r"([$₹£€])\s*([\d,.]+)\s*([KL])?", re.IGNORECASE)
_SUFFIX_MULTIPLIER = {"K": 1_000, "L": 100_000}


_LISTING_PAGE_MARKER_RE = re.compile(r'"@type"\s*:\s*"ItemList"')


def has_listing_marker(body_html: str) -> bool:
    """Whether the page actually rendered a real search-results page at
    all — every one, including a genuinely zero-result search, ships this
    JSON-LD marker. A page that never got past the bot wall does not, so
    this is what lets a caller tell "no matches" apart from "the request
    never actually got through".
    """
    return bool(_LISTING_PAGE_MARKER_RE.search(body_html))


def make_search_url(*, keyword: str, page: int) -> str:
    params: dict[str, str | int] = {"sc.keyword": keyword}
    if page > 1:
        params["p"] = page
    return f"{BASE_URL}{SEARCH_PATH}?{urlencode(params)}"


def is_job_entry(card_html: str) -> bool:
    return bool(_TITLE_HREF_RE.search(card_html)) and bool(_TITLE_ID_RE.search(card_html))


def _salary(card_html: str) -> Salary | None:
    match = _SALARY_RE.search(card_html)
    if not match:
        return None
    text = html_module.unescape(re.sub(r"<[^>]+>|<!--.*?-->", " ", match.group(1)))
    amounts = _SALARY_AMOUNT_RE.findall(text)
    if not amounts:
        return None
    values: list[int] = []
    currency = "USD"
    for symbol, number, suffix in amounts:
        currency = _CURRENCY_CODES.get(symbol, currency)
        multiplier = _SUFFIX_MULTIPLIER.get(suffix.upper(), 1)
        try:
            values.append(int(float(number.replace(",", "")) * multiplier))
        except ValueError:
            continue
    if not values:
        return None
    low, high = min(values), max(values)
    return Salary(
        min_amount=low,
        max_amount=high if high != low else None,
        currency=currency,
        period="year",
    )


def parse_card(card_html: str) -> JobPosting | None:
    """Parse one job card's outer HTML into a posting, or None if the card
    is unusable (no title link — a rendering glitch, not a real listing)."""
    if not is_job_entry(card_html):
        return None

    job_id_match = _TITLE_ID_RE.search(card_html)
    href_match = _TITLE_HREF_RE.search(card_html)
    title_match = _TITLE_TEXT_RE.search(card_html)
    company_match = _COMPANY_RE.search(card_html)
    location_match = _LOCATION_RE.search(card_html)
    desc_match = _DESC_RE.search(card_html)

    location = html_module.unescape(location_match.group(1)).strip() if location_match else ""
    url = href_match.group(1) if href_match else ""

    return JobPosting(
        source_provider=PROVIDER_ID,
        external_id=job_id_match.group(1) if job_id_match else "",
        title=html_module.unescape(title_match.group(1)).strip() if title_match else "",
        company_name=html_module.unescape(company_match.group(1)).strip() if company_match else "",
        url=url,
        apply_url=url or None,
        location=location or None,
        remote=any(token in location.lower() for token in _REMOTE_TOKENS),
        salary=_salary(card_html),
        description=html_module.unescape(desc_match.group(1)).strip() if desc_match else "",
    )
