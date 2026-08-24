"""Gradcracker: URL building and job-card parsing.

Gradcracker is a UK graduate-STEM board behind Cloudflare — every direct
fetch from this environment returned HTTP 403 (verified 2026-08-24), so
a real anti-detect browser session is required. The search URL shape and
the card structure below are grounded in a working scraper's verified
Playwright locators, not directly-observed production HTML — see
``tests/conftest.py`` for the specifics of that limitation.

Everything here is pure — no browser, no network. The browser mechanics
that get real card HTML live in ``client.py``.
"""

from __future__ import annotations

import re
from urllib.parse import urlencode

from careeros_gradcracker_provider.htmltree import Node, parse_html
from careeros_job_providers import JobPosting, Salary

PROVIDER_ID = "gradcracker"
BASE_URL = "https://www.gradcracker.com"
CARD_SELECTOR = "article[wire\\:key]"

_SLUG_STRIP_RE = re.compile(r"[^a-z0-9\s-]")
_SLUG_WS_RE = re.compile(r"\s+")
_SLUG_TRIM_RE = re.compile(r"^-+|-+$")

_REMOTE_TOKENS = ("remote",)
_SALARY_RE = re.compile(r"£\s*([\d,]+)(?:\s*-\s*£?\s*([\d,]+))?")


def slugify(text: str) -> str:
    lowered = _SLUG_STRIP_RE.sub("", text.strip().lower())
    collapsed = _SLUG_WS_RE.sub("-", lowered)
    return _SLUG_TRIM_RE.sub("", collapsed)


def make_search_url(*, role: str, region: str) -> str:
    """The Gradcracker list-page URL for one role in one UK region."""
    role_slug = slugify(role) or "graduate"
    region_slug = slugify(region) or "uk"
    path = f"/search/computing-technology/{role_slug}-graduate-jobs-in-{region_slug}"
    return f"{BASE_URL}{path}?{urlencode({'order': 'dateAdded'})}"


def is_job_entry(article_html: str) -> bool:
    node = parse_html(article_html)
    title_link = node.find_first("h2")
    if title_link is None:
        return False
    link = title_link.find_first("a")
    return link is not None and bool(link.attrs.get("href"))


def _absolute_url(href: str) -> str:
    if href.startswith(("http://", "https://")):
        return href
    return f"{BASE_URL}{href}" if href.startswith("/") else f"{BASE_URL}/{href}"


def _dt_dd_pairs(root: Node) -> dict[str, str]:
    """Every ``<dt>label</dt><dd>value</dd>`` pair, keyed by lowercased
    label text — Gradcracker's own presentation for Salary, Location,
    Degree required and Starting."""
    dl = root.find_first("dl")
    if dl is None:
        return {}
    pairs: dict[str, str] = {}
    pending_label: str | None = None
    for child in dl.children:
        if not isinstance(child, Node):
            continue
        if child.tag == "dt":
            pending_label = child.text().strip().lower()
        elif child.tag == "dd" and pending_label is not None:
            pairs[pending_label] = child.text().strip()
            pending_label = None
    return pairs


def _deadline_text(root: Node) -> str | None:
    for div in root.find_all("div"):
        text = div.text()
        if text.startswith("Deadline:"):
            return text[len("Deadline:") :].strip() or None
    return None


def _salary(text: str | None) -> Salary | None:
    if not text:
        return None
    match = _SALARY_RE.search(text)
    if not match:
        return None
    low_raw, high_raw = match.groups()
    low = int(low_raw.replace(",", ""))
    high = int(high_raw.replace(",", "")) if high_raw else None
    return Salary(
        min_amount=low,
        max_amount=high if high and high != low else None,
        currency="GBP",
        period="year",
    )


def parse_article(article_html: str) -> JobPosting | None:
    """Parse one job card's outer HTML into a posting, or None if the card
    is unusable (no title link — a rendering glitch, not a real listing)."""
    if not is_job_entry(article_html):
        return None

    root = parse_html(article_html)
    title_node = root.find_first("h2")
    link = title_node.find_first("a") if title_node else None
    if link is None:
        return None

    title = title_node.text().strip()
    href = link.attrs.get("href", "")

    figure = root.find_first("figure")
    employer = ""
    if figure is not None:
        img = figure.find_first("img")
        if img is not None:
            employer = img.attrs.get("alt", "").strip()

    disciplines_node = root.find_first("h3")
    disciplines = disciplines_node.text().strip() if disciplines_node else ""
    tags = [d.strip().lower() for d in disciplines.split(",") if d.strip()]

    pairs = _dt_dd_pairs(root)
    location = pairs.get("location")
    deadline = _deadline_text(root)
    degree = pairs.get("degree required")

    description_parts = [
        part
        for part in (
            f"Deadline: {deadline}" if deadline else None,
            f"Degree required: {degree}" if degree else None,
            f"Starting: {pairs['starting']}" if "starting" in pairs else None,
        )
        if part
    ]

    location_lower = (location or "").lower()
    return JobPosting(
        source_provider=PROVIDER_ID,
        external_id=href.rstrip("/").rsplit("/", 1)[-1] or href,
        title=title,
        company_name=employer,
        url=_absolute_url(href),
        location=location,
        remote=any(token in location_lower for token in _REMOTE_TOKENS),
        salary=_salary(pairs.get("salary")),
        description=" | ".join(description_parts),
        tags=tags,
    )
