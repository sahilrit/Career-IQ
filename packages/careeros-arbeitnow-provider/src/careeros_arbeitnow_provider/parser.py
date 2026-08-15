"""Normalizes Arbeitnow's raw JSON job entries into JobPosting records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from careeros_job_providers import EmploymentType, JobPosting

PROVIDER_ID = "arbeitnow"

_JOB_TYPE_MAP: dict[str, EmploymentType] = {
    "full time": EmploymentType.FULL_TIME,
    "part time": EmploymentType.PART_TIME,
    "contract": EmploymentType.CONTRACT,
    "freelance": EmploymentType.FREELANCE,
    "internship": EmploymentType.INTERNSHIP,
}


def _parse_employment_type(entry: dict[str, Any]) -> EmploymentType | None:
    for job_type in entry.get("job_types") or []:
        mapped = _JOB_TYPE_MAP.get(str(job_type).strip().lower())
        if mapped is not None:
            return mapped
    return None


def _parse_posted_at(entry: dict[str, Any]) -> datetime | None:
    raw = entry.get("created_at")
    if raw is None:
        return None
    try:
        return datetime.fromtimestamp(int(raw), tz=UTC)
    except (TypeError, ValueError, OSError):
        return None


def parse_job_entry(entry: dict[str, Any]) -> JobPosting:
    return JobPosting(
        source_provider=PROVIDER_ID,
        external_id=str(entry.get("slug") or entry.get("url") or ""),
        title=(entry.get("title") or "").strip(),
        company_name=(entry.get("company_name") or "").strip(),
        url=entry.get("url") or "",
        location=entry.get("location") or None,
        remote=bool(entry.get("remote", False)),
        salary=None,
        employment_type=_parse_employment_type(entry),
        description=entry.get("description") or "",
        tags=list(entry.get("tags") or []),
        posted_at=_parse_posted_at(entry),
    )
