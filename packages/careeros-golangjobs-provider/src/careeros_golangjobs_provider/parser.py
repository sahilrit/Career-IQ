"""Map golangjobs.tech Supabase rows onto ``JobPosting``."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from careeros_job_providers import JobPosting, Salary

PROVIDER_ID = "golangjobs"
_LISTING_BASE = "https://www.golangjobs.tech/golang-jobs"

_REMOTE_TOKENS = ("remote", "work from home", "anywhere", "wfh", "distributed")


def is_job_entry(row: dict[str, Any]) -> bool:
    return bool(row.get("id")) and bool(row.get("title"))


def _salary(row: dict[str, Any]) -> Salary | None:
    minimum = row.get("salary_min")
    maximum = row.get("salary_max")
    values = [v for v in (minimum, maximum) if isinstance(v, int | float) and v > 0]
    if not values:
        return None
    low, high = int(min(values)), int(max(values))
    return Salary(
        min_amount=low,
        max_amount=high if high != low else None,
        currency=str(row.get("salary_currency") or "USD"),
        period="year",
    )


def _posted_at(row: dict[str, Any]) -> datetime | None:
    raw = row.get("posted_at") or row.get("created_at")
    if not isinstance(raw, str) or not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _url(row: dict[str, Any]) -> str:
    # The direct apply link when the board has it; otherwise the listing page
    # built from the slug, so the posting always links somewhere real.
    apply_url = row.get("application_url")
    if isinstance(apply_url, str) and apply_url.strip():
        return apply_url.strip()
    slug = str(row.get("slug") or "").strip()
    return f"{_LISTING_BASE}/{slug}" if slug else _LISTING_BASE


def _tags(row: dict[str, Any]) -> list[str]:
    reqs = row.get("requirements")
    tags = (
        [str(r).strip().lower() for r in reqs if str(r).strip()] if isinstance(reqs, list) else []
    )
    return tags


def parse_job_entry(row: dict[str, Any]) -> JobPosting:
    text = f"{row.get('title', '')} {row.get('description', '')}".lower()
    return JobPosting(
        source_provider=PROVIDER_ID,
        external_id=str(row.get("id") or ""),
        title=str(row.get("title") or "").strip(),
        company_name=str(row.get("company") or "").strip(),
        url=_url(row),
        location=None,  # the board stores a city_id, not a resolvable label
        remote=any(token in text for token in _REMOTE_TOKENS),
        salary=_salary(row),
        description=str(row.get("description") or "").strip(),
        tags=_tags(row),
        posted_at=_posted_at(row),
    )
