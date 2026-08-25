"""UK Visa Jobs: request-field building and row parsing.

UK Visa Jobs is a client-rendered SPA with a credentialed search API
(``/ukvisa-api/api/fetch-jobs-data``) — there is no public API doc, so the
field names below (``company_name``, ``job_link``, ``min_salary`` /
``max_salary``, ``visa_acceptance``, ...) come from the real request/response
contract observed by a working integration against the live API, not
guessed.

Everything here is pure — no browser, no network. The login and the HTTP
calls that produce a real response body live in ``provider.py``.
"""

from __future__ import annotations

import json
from typing import Any

from careeros_job_providers import JobPosting, Salary

PROVIDER_ID = "ukvisajobs"
BASE_URL = "https://my.ukvisajobs.com"
SIGNIN_URL = f"{BASE_URL}/signin"
OPEN_JOBS_URL = (
    f"{BASE_URL}/open-jobs/1"
    "?is_global=0&sortBy=desc&visaAcceptance=false&applicants_outside_uk=false&pageNo=1"
)
API_URL = f"{BASE_URL}/ukvisa-api/api/fetch-jobs-data"
JOBS_PER_PAGE = 15

_REMOTE_TOKENS = ("remote", "work from home", "wfh")

# A row that only says "yes"/"no" per visa-related flag with no free-text
# description still carries real signal for this source specifically — a
# blank description would throw away the one thing UK Visa Jobs adds over
# a generic board.
_VISA_FLAG_LABELS = (
    ("visa_acceptance", "Visa acceptance"),
    ("applicants_outside_uk", "Accepts applicants outside the UK"),
    ("likely_to_sponsor", "Likely to sponsor"),
    ("definitely_sponsored", "Definitely sponsored"),
    ("new_entrant", "New entrant friendly"),
    ("student_graduate", "Student/graduate friendly"),
)


def build_search_form_fields(
    *, page_no: int, search_keyword: str | None, token: str
) -> dict[str, str]:
    """The multipart form fields the search API expects for one page."""
    return {
        "is_global": "0",
        "sortBy": "desc",
        "pageNo": str(page_no),
        "visaAcceptance": "false",
        "applicants_outside_uk": "false",
        "searchKeyword": search_keyword or "null",
        "token": token,
    }


def parse_search_response(body: str) -> dict[str, Any]:
    """The response's status, total job count, and job rows.

    Tolerant of anything malformed — an auth-error page, a shape change —
    by returning a zeroed-out shape rather than raising, so one bad
    response never crashes a run; the caller decides what an empty page
    means.
    """
    empty: dict[str, Any] = {"status": 0, "total_jobs": 0, "jobs": []}
    if not body:
        return empty
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return empty
    if not isinstance(payload, dict):
        return empty
    jobs = payload.get("jobs")
    return {
        "status": payload.get("status") if isinstance(payload.get("status"), int) else 0,
        "total_jobs": payload.get("totalJobs") if isinstance(payload.get("totalJobs"), int) else 0,
        "jobs": [row for row in jobs if isinstance(row, dict)] if isinstance(jobs, list) else [],
    }


def is_job_entry(row: dict[str, Any]) -> bool:
    return bool(row.get("id")) and bool(row.get("job_link"))


def is_auth_error(status_code: int, body_text: str) -> bool:
    if status_code in (401, 403):
        return True
    if status_code != 400:
        return False
    try:
        parsed = json.loads(body_text)
        if isinstance(parsed, dict):
            if parsed.get("errorType") == "expired":
                return True
            message = parsed.get("message")
            if isinstance(message, str) and "expired" in message.lower():
                return True
    except json.JSONDecodeError:
        pass
    return "expired" in body_text.lower()


def _to_positive_int(value: Any) -> int | None:
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _salary(row: dict[str, Any]) -> Salary | None:
    minimum = _to_positive_int(row.get("min_salary"))
    maximum = _to_positive_int(row.get("max_salary"))
    if minimum is None and maximum is None:
        return None
    return Salary(
        min_amount=minimum,
        max_amount=maximum if maximum != minimum else None,
        currency="GBP",
        period=str(row.get("salary_interval") or "year"),
    )


def _description(row: dict[str, Any]) -> str:
    stated = row.get("description")
    if isinstance(stated, str) and stated.strip():
        return stated.strip()
    flags = [
        label for field, label in _VISA_FLAG_LABELS if str(row.get(field, "")).lower() == "yes"
    ]
    return f"Visa sponsorship: {', '.join(flags)}" if flags else ""


def _tags(row: dict[str, Any]) -> list[str]:
    tags = []
    for field in ("job_industry", "job_type", "job_level"):
        value = row.get(field)
        if isinstance(value, str) and value.strip():
            tags.append(value.strip().lower())
    return tags


def parse_job_entry(row: dict[str, Any]) -> JobPosting:
    job_link = str(row.get("job_link") or "")
    city = str(row.get("city") or "").strip()
    return JobPosting(
        source_provider=PROVIDER_ID,
        external_id=str(row.get("id") or ""),
        title=str(row.get("title") or "").strip(),
        company_name=str(row.get("company_name") or "").strip(),
        url=job_link,
        apply_url=job_link or None,
        location=city or None,
        remote=any(token in city.lower() for token in _REMOTE_TOKENS),
        salary=_salary(row),
        description=_description(row),
        tags=_tags(row),
    )
