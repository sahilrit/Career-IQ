"""Read Hiring Cafe's server-rendered search payload.

Hiring Cafe is a Next.js app that encodes the whole search state in the
query string and ships the results inside the page as ``__NEXT_DATA__``.
There is no API to call: we request the page a browser would request and
read the JSON the server already put there.

Search hits carry no job description — only Hiring Cafe's own structured
extraction of the posting. That extraction is genuinely useful (skills,
requirements, activities), so we compose a description from it rather
than making a second request per job.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from careeros_job_providers import EmploymentType, JobPosting, JobProviderError, Salary

PROVIDER_ID = "hiringcafe"
JOB_PAGE_TEMPLATE = "https://hiring.cafe/job/{job_id}"

_NEXT_DATA_RE = re.compile(
    r'<script[^>]*id="__NEXT_DATA__"[^>]*>\s*(.*?)\s*</script>', re.DOTALL | re.IGNORECASE
)

# Same markers the challenge shows regardless of which variant Cloudflare
# serves; the managed challenge returns HTTP 200, so status alone won't do.
_CHALLENGE_MARKERS = (
    "cf-turnstile",
    "cf_chl_opt",
    "Just a moment...",
    "challenges.cloudflare.com",
    "cf-browser-verification",
)

_EMPLOYMENT_TYPES = {
    "full time": EmploymentType.FULL_TIME,
    "part time": EmploymentType.PART_TIME,
    "contract": EmploymentType.CONTRACT,
    "contractor": EmploymentType.CONTRACT,
    "temporary": EmploymentType.CONTRACT,
    "freelance": EmploymentType.FREELANCE,
    "internship": EmploymentType.INTERNSHIP,
}


class HiringCafeChallengeError(JobProviderError):
    """Hiring Cafe served a bot challenge instead of search results.

    Kept distinct from a generic failure so the caller can tell "blocked"
    from "broken" — the two need different responses.
    """


class HiringCafeSsrPage(BaseModel):
    hits: list[dict[str, Any]]
    page: int
    total_count: int | None
    is_last_page: bool


def _looks_like_a_challenge(html: str) -> bool:
    return any(marker in html for marker in _CHALLENGE_MARKERS)


def parse_ssr_page(html: str) -> HiringCafeSsrPage:
    if _looks_like_a_challenge(html):
        raise HiringCafeChallengeError(
            "Hiring Cafe returned a bot challenge instead of search results"
        )

    match = _NEXT_DATA_RE.search(html)
    if not match:
        raise JobProviderError("Hiring Cafe response contained no __NEXT_DATA__ payload")

    try:
        page_props = json.loads(match.group(1))["props"]["pageProps"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise JobProviderError(f"Hiring Cafe payload was not in the expected shape: {exc}") from exc

    hits = page_props.get("ssrHits")
    if not isinstance(hits, list):
        raise JobProviderError("Hiring Cafe payload contained no ssrHits list")

    return HiringCafeSsrPage(
        hits=[hit for hit in hits if isinstance(hit, dict)],
        page=int(page_props.get("ssrPage") or 0),
        total_count=page_props.get("ssrTotalCount"),
        is_last_page=bool(page_props.get("ssrIsLastPage")),
    )


def is_job_entry(hit: dict[str, Any]) -> bool:
    if hit.get("is_expired"):
        return False
    title = (hit.get("job_information") or {}).get("title")
    return bool(hit.get("id")) and bool(title) and bool(hit.get("apply_url"))


def _v5(hit: dict[str, Any]) -> dict[str, Any]:
    return hit.get("v5_processed_job_data") or {}


def _salary(v5: dict[str, Any]) -> Salary | None:
    minimum = v5.get("yearly_min_compensation")
    maximum = v5.get("yearly_max_compensation")
    values = [int(v) for v in (minimum, maximum) if isinstance(v, int | float) and v > 0]
    if not values:
        return None
    return Salary(
        min_amount=int(minimum) if isinstance(minimum, int | float) and minimum > 0 else None,
        max_amount=int(maximum) if isinstance(maximum, int | float) and maximum > 0 else None,
        currency=str(v5.get("listed_compensation_currency") or "USD"),
        period="year",
    )


def _employment_type(v5: dict[str, Any]) -> EmploymentType | None:
    for value in v5.get("commitment") or []:
        mapped = _EMPLOYMENT_TYPES.get(str(value).strip().lower())
        if mapped:
            return mapped
    return None


def _posted_at(v5: dict[str, Any]) -> datetime | None:
    raw = v5.get("estimated_publish_date")
    if not isinstance(raw, str) or not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def _tags(v5: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    seen: set[str] = set()
    candidates = [
        *(v5.get("technical_tools") or []),
        v5.get("job_category"),
        v5.get("seniority_level"),
    ]
    for value in candidates:
        if not value:
            continue
        tag = str(value).strip().lower()
        if tag and tag not in seen:
            seen.add(tag)
            tags.append(tag)
    return tags


def _description(v5: dict[str, Any]) -> str:
    """Compose readable text from Hiring Cafe's structured extraction.

    Kept in the same order a person would read it — what the job needs,
    what the job does, what it uses — because this text is what the match
    scorer tokenizes.
    """
    sections: list[str] = []
    summary = str(v5.get("requirements_summary") or "").strip()
    if summary:
        sections.append(summary)

    activities = [str(a).strip() for a in (v5.get("role_activities") or []) if str(a).strip()]
    if activities:
        sections.append("Responsibilities: " + ", ".join(activities) + ".")

    tools = [str(t).strip() for t in (v5.get("technical_tools") or []) if str(t).strip()]
    if tools:
        sections.append("Tools: " + ", ".join(tools) + ".")

    return "\n\n".join(sections)


def parse_job_entry(hit: dict[str, Any]) -> JobPosting:
    v5 = _v5(hit)
    title = (hit.get("job_information") or {}).get("title") or v5.get("core_job_title") or ""
    location = str(v5.get("formatted_workplace_location") or "").strip()
    return JobPosting(
        source_provider=PROVIDER_ID,
        external_id=str(hit.get("id") or ""),
        title=str(title).strip(),
        company_name=str(v5.get("company_name") or "").strip(),
        # The apply URL goes straight to the employer's own ATS, which is
        # where the candidate has to end up anyway.
        url=str(hit.get("apply_url") or JOB_PAGE_TEMPLATE.format(job_id=hit.get("id"))),
        location=location or None,
        remote=str(v5.get("workplace_type") or "").strip().lower() == "remote",
        salary=_salary(v5),
        employment_type=_employment_type(v5),
        description=_description(v5),
        tags=_tags(v5),
        posted_at=_posted_at(v5),
    )
