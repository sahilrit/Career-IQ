"""Naukri: URL building and row parsing.

Naukri is India's largest job board and a client-rendered SPA whose
search API (``/jobapi/v3/search``) requires a real browser session — a
plain HTTP request to it returns HTTP 406 "recaptcha required" (verified
live 2026-08-24). The URL shape and the ``jobDetails[]`` row shape below
are grounded in a working scraper's source, not guessed: the field names
(``jdURL``, ``placeholders``, ``salaryDetail``, ...) come from code that
maps this exact response into job postings in production.

Everything here is pure — no browser, no network. The browser mechanics
that get a real response body live in ``client.py``.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode

from careeros_job_providers import JobPosting, Salary

PROVIDER_ID = "naukri"
BASE_URL = "https://www.naukri.com"
DEFAULT_FRESHNESS = "7"

_SLUG_STRIP_RE = re.compile(r"[^a-z0-9\s-]")
_SLUG_WS_RE = re.compile(r"\s+")
_SLUG_TRIM_RE = re.compile(r"^-+|-+$")

_REMOTE_TOKENS = ("remote", "work from home", "wfh")


def slugify_keyword(keyword: str) -> str:
    lowered = _SLUG_STRIP_RE.sub("", keyword.strip().lower())
    collapsed = _SLUG_WS_RE.sub("-", lowered)
    return _SLUG_TRIM_RE.sub("", collapsed)


def make_search_url(
    *, keyword: str, location: str | None = None, freshness: str = DEFAULT_FRESHNESS
) -> str:
    """The Naukri search-page URL for one keyword (+ optional location).

    Navigating here in a real browser is what makes the SPA call its own
    search API with a valid session; that API response — not this page's
    HTML — is what the provider actually reads.
    """
    keyword_slug = slugify_keyword(keyword) or "jobs"
    location = location.strip() if location else None
    location_slug = slugify_keyword(location) if location else ""
    path = f"/{keyword_slug}-jobs-in-{location_slug}" if location_slug else f"/{keyword_slug}-jobs"

    params: dict[str, str] = {"k": keyword}
    if location:
        params["l"] = location
    params["jobAge"] = freshness

    return f"{BASE_URL}{path}?{urlencode(params)}"


def parse_search_response(body: str) -> list[dict[str, Any]]:
    """Every row in a search API response's ``jobDetails`` array.

    Tolerant of anything malformed — a challenge page, a shape change — by
    returning an empty list rather than raising, so one bad response never
    crashes a run; the caller decides what an empty page means.
    """
    if not body:
        return []
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, dict):
        return []
    rows = payload.get("jobDetails")
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def is_job_entry(row: dict[str, Any]) -> bool:
    return bool(row.get("jdURL")) and bool(row.get("title"))


def _absolute_url(path_or_url: str) -> str:
    if path_or_url.startswith(("http://", "https://")):
        return path_or_url
    if path_or_url.startswith("/"):
        return f"{BASE_URL}{path_or_url}"
    return f"{BASE_URL}/{path_or_url}"


def _placeholder(row: dict[str, Any], kind: str) -> str | None:
    for placeholder in row.get("placeholders") or []:
        if isinstance(placeholder, dict) and placeholder.get("type") == kind:
            label = placeholder.get("label")
            return str(label).strip() if label else None
    return None


def _salary(row: dict[str, Any]) -> Salary | None:
    detail = row.get("salaryDetail")
    if not isinstance(detail, dict) or detail.get("hideSalary") is True:
        return None
    minimum, maximum = detail.get("minimumSalary"), detail.get("maximumSalary")
    values = [v for v in (minimum, maximum) if isinstance(v, int | float) and v > 0]
    if not values:
        return None
    low, high = int(min(values)), int(max(values))
    return Salary(
        min_amount=low,
        max_amount=high if high != low else None,
        currency=str(detail.get("currency") or "INR"),
        period="year",
    )


def _posted_at(row: dict[str, Any]) -> datetime | None:
    raw = row.get("createdDate")
    if not isinstance(raw, int | float):
        return None
    try:
        return datetime.fromtimestamp(raw / 1000, tz=UTC)
    except (ValueError, OSError):
        return None


def _tags(row: dict[str, Any]) -> list[str]:
    raw = row.get("tagsAndSkills")
    if not isinstance(raw, str) or not raw.strip():
        return []
    return [tag.strip().lower() for tag in raw.split(",") if tag.strip()]


def parse_job_entry(row: dict[str, Any]) -> JobPosting:
    jd_url = str(row.get("jdURL") or "")
    location = _placeholder(row, "location") or ""
    return JobPosting(
        source_provider=PROVIDER_ID,
        external_id=str(row.get("jobId") or ""),
        title=str(row.get("title") or "").strip(),
        company_name=str(row.get("companyName") or "").strip(),
        url=_absolute_url(jd_url) if jd_url else "",
        location=location or None,
        remote=any(token in location.lower() for token in _REMOTE_TOKENS),
        salary=_salary(row),
        description=str(row.get("jobDescription") or "").strip(),
        tags=_tags(row),
        posted_at=_posted_at(row),
    )
