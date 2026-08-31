"""Ashby — public job-board API, no key.

``includeCompensation=true`` is what makes salary usable, but Ashby quotes it
per interval (hourly/monthly/annual). Comparing a monthly figure straight
against an annual expectation silently mis-scores every one of those postings,
so everything is annualized on the way in.

Ashby also carries ``secondaryLocations``; dropping them loses every extra
city a role is open to.
"""

from __future__ import annotations

from typing import Any

from careeros_ats_providers.adapter import AtsAdapter, BoardEntry
from careeros_ats_providers.http import AtsHttp
from careeros_ats_providers.normalize import (
    annualized_salary,
    html_to_text,
    looks_remote,
    merge_locations,
    to_datetime,
)
from careeros_job_providers import EmploymentType, JobPosting

_TYPE_MAP = {
    "fulltime": EmploymentType.FULL_TIME,
    "full-time": EmploymentType.FULL_TIME,
    "parttime": EmploymentType.PART_TIME,
    "part-time": EmploymentType.PART_TIME,
    "contract": EmploymentType.CONTRACT,
    "temporary": EmploymentType.CONTRACT,
    "intern": EmploymentType.INTERNSHIP,
    "internship": EmploymentType.INTERNSHIP,
}


class AshbyAdapter(AtsAdapter):
    ats_id = "ashby"
    allowed_hosts = frozenset({"api.ashbyhq.com", "jobs.ashbyhq.com"})

    def fetch_board(self, entry: BoardEntry, http: AtsHttp) -> list[dict[str, Any]]:
        url = f"https://api.ashbyhq.com/posting-api/job-board/{entry.slug}?includeCompensation=true"
        payload = http.get_json(self.check(url))
        jobs = payload.get("jobs") if isinstance(payload, dict) else None
        return [j for j in (jobs or []) if isinstance(j, dict)]

    def to_posting(self, raw: dict[str, Any], entry: BoardEntry) -> JobPosting | None:
        url = raw.get("jobUrl") or raw.get("applyUrl")
        if not url:
            return None
        secondary = raw.get("secondaryLocations") or []
        secondary_names = [
            s.get("location") for s in secondary if isinstance(s, dict) and s.get("location")
        ]
        location = merge_locations(raw.get("location"), secondary_names)
        compensation = raw.get("compensation") or {}
        salary = annualized_salary(
            compensation.get("minValue"),
            compensation.get("maxValue"),
            compensation.get("currency"),
            compensation.get("interval"),
        )
        description = raw.get("descriptionPlain")
        if not isinstance(description, str) or not description.strip():
            description = html_to_text(raw.get("descriptionHtml") or raw.get("description"))
        employment = (raw.get("employmentType") or "").strip().lower().replace(" ", "")
        return JobPosting(
            source_provider=self.ats_id,
            external_id=str(raw.get("id") or url),
            title=(raw.get("title") or "").strip(),
            company_name=entry.name,
            url=url,
            # Ashby's posting page is a React app that routes the form to
            # /application; there is no <a> to follow, so derive it.
            apply_url=raw.get("applyUrl") or f"{url.rstrip('/')}/application",
            location=location or None,
            remote=bool(raw.get("isRemote")) or looks_remote(location),
            salary=salary,
            employment_type=_TYPE_MAP.get(employment),
            description=description or "",
            posted_at=to_datetime(raw.get("publishedAt") or raw.get("updatedAt")),
        )

    def probe_entry(self) -> BoardEntry:
        return BoardEntry("ramp", "Ramp")
