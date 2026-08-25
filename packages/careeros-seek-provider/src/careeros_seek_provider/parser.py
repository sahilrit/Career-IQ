"""Seek: URL building and row parsing.

Field names (``salaryLabel``, ``listingDate``, ``workTypes``,
``classifications``, ...) come from a live capture of Seek's own public
search API response (``/api/jobsearch/v5/search``), verified 2026-08-26 —
see ``client.py`` for the request that produces it.

Everything here is pure — no network.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

from careeros_job_providers import EmploymentType, JobPosting, Salary

PROVIDER_ID = "seek"
BASE_URL = "https://www.seek.com.au"
API_URL = f"{BASE_URL}/api/jobsearch/v5/search"

_REMOTE_TOKENS = ("remote", "work from home", "wfh")

_SALARY_RE = re.compile(r"\$\s*([\d,]+)")
_HOURLY_RE = re.compile(r"\bhour\b", re.IGNORECASE)

_WORK_TYPE_MAP = {
    "full time": EmploymentType.FULL_TIME,
    "part time": EmploymentType.PART_TIME,
    "contract/temp": EmploymentType.CONTRACT,
    "casual/vacation": EmploymentType.PART_TIME,
}


def make_job_url(job_id: str) -> str:
    return f"{BASE_URL}/job/{job_id}"


def parse_search_response(body: str) -> dict[str, Any]:
    """The response's total match count and job rows.

    Tolerant of anything malformed by returning a zeroed-out shape rather
    than raising, so one bad response never crashes a run.
    """
    empty: dict[str, Any] = {"total_count": 0, "jobs": []}
    if not body:
        return empty
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return empty
    if not isinstance(payload, dict):
        return empty
    jobs = payload.get("data")
    total = payload.get("totalCount")
    return {
        "total_count": total if isinstance(total, int) else 0,
        "jobs": [row for row in jobs if isinstance(row, dict)] if isinstance(jobs, list) else [],
    }


def is_job_entry(row: dict[str, Any]) -> bool:
    return bool(row.get("id")) and bool(row.get("title"))


def _location_label(row: dict[str, Any]) -> str:
    locations = row.get("locations")
    if not isinstance(locations, list) or not locations:
        return ""
    first = locations[0]
    if not isinstance(first, dict):
        return ""
    return str(first.get("label") or "").strip()


def _salary(row: dict[str, Any]) -> Salary | None:
    label = row.get("salaryLabel")
    if not isinstance(label, str) or not label.strip():
        return None
    amounts = [int(m.replace(",", "")) for m in _SALARY_RE.findall(label)]
    amounts = [amount for amount in amounts if amount > 0]
    if not amounts:
        return None
    low, high = min(amounts), max(amounts)
    period = "hour" if _HOURLY_RE.search(label) else "year"
    return Salary(
        min_amount=low,
        max_amount=high if high != low else None,
        currency="AUD",
        period=period,
    )


def _posted_at(row: dict[str, Any]) -> datetime | None:
    raw = row.get("listingDate")
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _tags(row: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    for entry in row.get("classifications") or []:
        if not isinstance(entry, dict):
            continue
        for key in ("classification", "subclassification"):
            described = entry.get(key)
            if isinstance(described, dict):
                description = described.get("description")
                if isinstance(description, str) and description.strip():
                    tags.append(description.strip().lower())
    return tags


def _employment_type(row: dict[str, Any]) -> EmploymentType | None:
    work_types = row.get("workTypes")
    if not isinstance(work_types, list):
        return None
    for work_type in work_types:
        mapped = _WORK_TYPE_MAP.get(str(work_type).strip().lower())
        if mapped is not None:
            return mapped
    return None


def parse_job_entry(row: dict[str, Any]) -> JobPosting:
    job_id = str(row.get("id") or "")
    location = _location_label(row)
    url = make_job_url(job_id) if job_id else ""
    return JobPosting(
        source_provider=PROVIDER_ID,
        external_id=job_id,
        title=str(row.get("title") or "").strip(),
        company_name=str(row.get("companyName") or "").strip(),
        url=url,
        apply_url=url or None,
        location=location or None,
        remote=any(token in location.lower() for token in _REMOTE_TOKENS),
        salary=_salary(row),
        employment_type=_employment_type(row),
        description=str(row.get("teaser") or "").strip(),
        tags=_tags(row),
        posted_at=_posted_at(row),
    )
