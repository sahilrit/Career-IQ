"""Map Adzuna search results onto ``JobPosting``."""

from __future__ import annotations

import html
import re
from datetime import datetime
from typing import Any

from careeros_job_providers import EmploymentType, JobPosting, Salary

PROVIDER_ID = "adzuna"

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

_REMOTE_TOKENS = ("remote", "work from home", "anywhere", "wfh")

_CONTRACT_TIMES = {
    "full_time": EmploymentType.FULL_TIME,
    "part_time": EmploymentType.PART_TIME,
}
_CONTRACT_TYPES = {
    "contract": EmploymentType.CONTRACT,
    "permanent": EmploymentType.FULL_TIME,
}


def _clean(raw: Any) -> str:
    """Adzuna wraps matched query terms in real ``<strong>`` tags, in both the
    title and the description snippet."""
    return _WS_RE.sub(" ", html.unescape(_TAG_RE.sub("", str(raw or "")))).strip()


def is_job_entry(result: dict[str, Any]) -> bool:
    return bool(result.get("id")) and bool(result.get("redirect_url"))


def _salary(result: dict[str, Any]) -> Salary | None:
    """Adzuna fills in an *estimated* salary when the advert states none, and
    flags it with ``salary_is_predicted``. Treating an estimate as a stated
    figure would let a guess satisfy a candidate's minimum-salary filter, so
    predicted salaries are dropped entirely.
    """
    if str(result.get("salary_is_predicted") or "0") == "1":
        return None

    minimum = result.get("salary_min")
    maximum = result.get("salary_max")
    values = [v for v in (minimum, maximum) if isinstance(v, int | float) and v > 0]
    if not values:
        return None

    low = int(min(values))
    high = int(max(values))
    return Salary(
        min_amount=low,
        max_amount=high if high != low else None,
        currency=str(result.get("salary_currency") or "GBP"),
        period="year",
    )


def _posted_at(result: dict[str, Any]) -> datetime | None:
    raw = result.get("created")
    if not isinstance(raw, str) or not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _employment_type(result: dict[str, Any]) -> EmploymentType | None:
    contract_time = str(result.get("contract_time") or "").lower()
    if contract_time in _CONTRACT_TIMES:
        return _CONTRACT_TIMES[contract_time]
    return _CONTRACT_TYPES.get(str(result.get("contract_type") or "").lower())


def _tags(result: dict[str, Any]) -> list[str]:
    label = (result.get("category") or {}).get("label")
    return [str(label).strip().lower()] if label else []


def parse_job_entry(result: dict[str, Any]) -> JobPosting:
    location = _clean((result.get("location") or {}).get("display_name"))
    return JobPosting(
        source_provider=PROVIDER_ID,
        external_id=str(result.get("id") or ""),
        title=_clean(result.get("title")),
        company_name=_clean((result.get("company") or {}).get("display_name")),
        url=str(result.get("redirect_url") or ""),
        location=location or None,
        remote=any(token in location.lower() for token in _REMOTE_TOKENS),
        salary=_salary(result),
        employment_type=_employment_type(result),
        description=_clean(result.get("description")),
        tags=_tags(result),
        posted_at=_posted_at(result),
    )
