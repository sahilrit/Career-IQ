"""Normalizes Himalayas' raw JSON job entries into JobPosting records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from careeros_job_providers import EmploymentType, JobPosting, Salary

PROVIDER_ID = "himalayas"

_EMPLOYMENT_TYPES = {
    "full time": EmploymentType.FULL_TIME,
    "part time": EmploymentType.PART_TIME,
    "contractor": EmploymentType.CONTRACT,
    "contract": EmploymentType.CONTRACT,
    "freelance": EmploymentType.FREELANCE,
    "internship": EmploymentType.INTERNSHIP,
}


def is_job_entry(entry: dict[str, Any]) -> bool:
    return bool(entry.get("title")) and bool(entry.get("applicationLink") or entry.get("guid"))


def _parse_salary(entry: dict[str, Any]) -> Salary | None:
    min_amount = entry.get("minSalary")
    max_amount = entry.get("maxSalary")
    if min_amount is None and max_amount is None:
        return None
    period = "hour" if entry.get("salaryPeriod") == "hourly" else "year"
    return Salary(
        min_amount=int(min_amount) if min_amount is not None else None,
        max_amount=int(max_amount) if max_amount is not None else None,
        currency=entry.get("currency") or "USD",
        period=period,
    )


def _parse_posted_at(entry: dict[str, Any]) -> datetime | None:
    raw = entry.get("pubDate")
    if not raw:
        return None
    try:
        return datetime.fromtimestamp(int(raw), tz=UTC)
    except (ValueError, OSError, OverflowError):
        return None


def _parse_location(entry: dict[str, Any]) -> str | None:
    restrictions = entry.get("locationRestrictions") or []
    return ", ".join(restrictions) if restrictions else None


def _parse_company_name(entry: dict[str, Any]) -> str:
    name = (entry.get("companyName") or "").strip()
    # Some upstream entries carry the literal placeholder "name"; the slug
    # ("the-spark-group") is reliable, so title-case it as a fallback.
    if name.lower() in ("", "name"):
        slug = (entry.get("companySlug") or "").strip()
        return slug.replace("-", " ").title() if slug else name
    return name


def parse_job_entry(entry: dict[str, Any]) -> JobPosting:
    tags = [tag.replace("-", " ").lower() for tag in entry.get("categories") or []]
    tags += [tag.replace("-", " ").lower() for tag in entry.get("parentCategories") or []]
    employment_raw = (entry.get("employmentType") or "").strip().lower()
    return JobPosting(
        source_provider=PROVIDER_ID,
        external_id=str(entry.get("guid") or entry.get("applicationLink")),
        title=(entry.get("title") or "").strip(),
        company_name=_parse_company_name(entry),
        url=entry.get("applicationLink") or entry.get("guid") or "",
        location=_parse_location(entry),
        remote=True,  # Himalayas is a remote-only job board by definition
        salary=_parse_salary(entry),
        employment_type=_EMPLOYMENT_TYPES.get(employment_raw, EmploymentType.FULL_TIME),
        description=entry.get("description") or entry.get("excerpt") or "",
        tags=tags,
        posted_at=_parse_posted_at(entry),
    )
