"""Map Working Nomads search documents onto ``JobPosting``."""

from __future__ import annotations

import html
import re
from datetime import datetime
from typing import Any

from careeros_job_providers import EmploymentType, JobPosting, Salary

PROVIDER_ID = "workingnomads"

JOB_URL_TEMPLATE = "https://www.workingnomads.com/jobs/{slug}"

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

# Working Nomads' own position_type codes.
_EMPLOYMENT_TYPES = {
    "ft": EmploymentType.FULL_TIME,
    "full_time": EmploymentType.FULL_TIME,
    "pt": EmploymentType.PART_TIME,
    "part_time": EmploymentType.PART_TIME,
    "contract": EmploymentType.CONTRACT,
    "freelance": EmploymentType.FREELANCE,
    "internship": EmploymentType.INTERNSHIP,
}


def is_job_entry(doc: dict[str, Any]) -> bool:
    """Expired postings stay in the index; they are not worth showing."""
    if doc.get("expired"):
        return False
    return bool(doc.get("id")) and bool(doc.get("title"))


def _plain_text(raw: str | None) -> str:
    """Strip tags, then decode entities — in that order, so an escaped
    ``&lt;p&gt;`` in the copy isn't mistaken for markup and eaten."""
    stripped = _TAG_RE.sub(" ", raw or "")
    return _WS_RE.sub(" ", html.unescape(stripped)).strip()


def _tags(doc: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    seen: set[str] = set()
    raw_tags = doc.get("tags") or []
    if isinstance(raw_tags, str):
        raw_tags = raw_tags.split(",")
    for value in [*raw_tags, *(doc.get("all_tags") or []), doc.get("category_name")]:
        if not value:
            continue
        tag = str(value).strip().lower()
        if tag and tag not in seen:
            seen.add(tag)
            tags.append(tag)
    return tags


def _salary(doc: dict[str, Any]) -> Salary | None:
    """``annual_salary_usd`` is the indexed, already-normalised figure. The
    free-text ``salary_range`` is left in the description rather than parsed
    a second time."""
    amount = doc.get("annual_salary_usd")
    if not isinstance(amount, int | float) or amount <= 0:
        return None
    return Salary(min_amount=None, max_amount=int(amount), currency="USD", period="year")


def _posted_at(doc: dict[str, Any]) -> datetime | None:
    raw = doc.get("pub_date")
    if not isinstance(raw, str) or not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _location(doc: dict[str, Any]) -> str | None:
    locations = doc.get("locations") or []
    if isinstance(locations, str):
        locations = [locations]
    parts = [str(part).strip() for part in locations if str(part).strip()]
    extra = str(doc.get("location_base") or "").strip()
    if extra and extra not in parts:
        parts.append(extra)
    return ", ".join(parts) or None


def _url(doc: dict[str, Any]) -> str:
    slug = str(doc.get("slug") or "").strip()
    if slug:
        return JOB_URL_TEMPLATE.format(slug=slug)
    # Fall back to the employer's own apply link rather than returning
    # a posting with no way to reach it.
    return str(doc.get("apply_url") or "")


def parse_job_entry(doc: dict[str, Any]) -> JobPosting:
    return JobPosting(
        source_provider=PROVIDER_ID,
        external_id=str(doc.get("id") or doc.get("external_id") or ""),
        title=str(doc.get("title") or "").strip(),
        company_name=str(doc.get("company") or doc.get("company_name") or "").strip(),
        url=_url(doc),
        # The employer's own apply link (a real ATS such as applytojob.com),
        # which WorkingNomads carries alongside its listing-page slug. Kept so
        # the autopilot can reach the actual form, not just the listing.
        apply_url=str(doc.get("apply_url") or "") or None,
        location=_location(doc),
        remote=True,
        salary=_salary(doc),
        employment_type=_EMPLOYMENT_TYPES.get(str(doc.get("position_type") or "").lower()),
        description=_plain_text(doc.get("description")),
        tags=_tags(doc),
        posted_at=_posted_at(doc),
    )
