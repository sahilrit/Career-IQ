"""ZipRecruiter: URL building and JSON-LD job listing extraction.

ZipRecruiter's search-results page embeds a ``<script
type="application/ld+json">`` block describing every result as a schema.org
``ItemList`` — verified against a live page (2026-08-26) after a real
Camoufox session passed the site's Cloudflare challenge. Each item is just
``{name, url}``, but the URL itself is structured
(``/c/{company}/Job/{title-slug}/-in-{location}?jid={id}``), so company,
location, and a stable external id are all derived from it rather than
needing to correlate against the rendered job cards (which duplicate
across the list view and a selected-job detail pane).

Everything here is pure — no browser, no network. The Camoufox session
that produces real page HTML lives in ``provider.py``.
"""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import parse_qs, quote_plus, unquote, urlencode, urlparse

from careeros_job_providers import JobPosting

PROVIDER_ID = "ziprecruiter"
BASE_URL = "https://www.ziprecruiter.com"
SEARCH_PATH = "/jobs-search"

_REMOTE_TOKENS = ("remote",)

_LD_JSON_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.DOTALL)
_URL_PARTS_RE = re.compile(r"/c/(?P<company>[^/]+)/Job/[^/]+/-in-(?P<location>[^?]+)")


def make_search_url(*, keyword: str, location: str | None, page: int) -> str:
    params: dict[str, str | int] = {"search": keyword, "page": max(1, page)}
    if location:
        params["location"] = location
    return f"{BASE_URL}{SEARCH_PATH}?{urlencode(params, quote_via=quote_plus)}"


def has_ld_json_block(html: str) -> bool:
    """Whether the page shipped its JSON-LD listing block at all.

    Every real result page — including a genuinely zero-result one — has
    this block; a page that never resolved the Cloudflare challenge (still
    showing the interstitial) does not. This is what lets a caller tell
    "no matches" apart from "the request never actually got through".
    """
    return bool(_LD_JSON_RE.search(html))


def extract_ld_json_items(html: str) -> list[dict[str, Any]]:
    """Every entry in the page's embedded JSON-LD ``ItemList``.

    Tolerant of anything malformed — a layout change, no listings on the
    page — by returning an empty list rather than raising, so one bad page
    never crashes a run.
    """
    match = _LD_JSON_RE.search(html)
    if not match:
        return []
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, dict):
        return []
    items = payload.get("itemListElement")
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def is_job_entry(item: dict[str, Any]) -> bool:
    return bool(item.get("url")) and bool(item.get("name"))


def _dehyphenate(segment: str) -> str:
    return unquote(segment).replace("-", " ").strip()


def _url_parts(url: str) -> tuple[str, str, str]:
    """(external_id, company_name, location) derived from a job URL, each
    empty when the URL isn't the expected shape rather than raising."""
    jid = parse_qs(urlparse(url).query).get("jid", [""])[0]
    match = _URL_PARTS_RE.search(url)
    if not match:
        return jid, "", ""
    company = _dehyphenate(match.group("company"))
    location = _dehyphenate(match.group("location")).replace(",", ", ")
    location = re.sub(r"\s+,", ",", location).strip()
    return jid, company, location


def parse_job_entry(item: dict[str, Any]) -> JobPosting:
    url = str(item.get("url") or "")
    external_id, company, location = _url_parts(url)
    location_lower = location.lower()
    return JobPosting(
        source_provider=PROVIDER_ID,
        external_id=external_id,
        title=str(item.get("name") or "").strip(),
        company_name=company,
        url=url,
        apply_url=url or None,
        location=location or None,
        remote=any(token in location_lower for token in _REMOTE_TOKENS),
    )
