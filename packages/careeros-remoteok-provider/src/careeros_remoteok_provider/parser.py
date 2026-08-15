"""Normalizes RemoteOK's raw JSON job entries into JobPosting records."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from careeros_job_providers import EmploymentType, JobPosting, Salary

PROVIDER_ID = "remoteok"


def is_job_entry(entry: dict[str, Any]) -> bool:
    """RemoteOK's feed starts with a non-job legal/metadata object; skip it."""
    return "id" in entry and "position" in entry


def _parse_salary(entry: dict[str, Any]) -> Salary | None:
    min_amount = entry.get("salary_min")
    max_amount = entry.get("salary_max")
    if min_amount is None and max_amount is None:
        return None
    return Salary(min_amount=min_amount, max_amount=max_amount, currency="USD", period="year")


def _parse_posted_at(entry: dict[str, Any]) -> datetime | None:
    raw = entry.get("date")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_job_entry(entry: dict[str, Any]) -> JobPosting:
    return JobPosting(
        source_provider=PROVIDER_ID,
        external_id=str(entry["id"]),
        title=(entry.get("position") or "").strip(),
        company_name=(entry.get("company") or "").strip(),
        url=entry.get("url") or entry.get("apply_url") or "",
        location=entry.get("location") or None,
        remote=True,  # RemoteOK is a remote-only job board by definition
        salary=_parse_salary(entry),
        employment_type=EmploymentType.FULL_TIME,
        description=entry.get("description") or "",
        tags=list(entry.get("tags") or []),
        posted_at=_parse_posted_at(entry),
    )
