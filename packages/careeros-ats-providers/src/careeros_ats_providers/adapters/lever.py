"""Lever — public postings API, no key.

Lever ships ``descriptionPlain`` for free in the list response, so unlike most
ATSes there is never a per-job fetch. It also splits location across
``categories.location`` and ``categories.allLocations``; keeping only the
first drops every additional city a role is open to.
"""

from __future__ import annotations

from typing import Any

from careeros_ats_providers.adapter import AtsAdapter, BoardEntry
from careeros_ats_providers.http import AtsHttp
from careeros_ats_providers.normalize import (
    html_to_text,
    looks_remote,
    merge_locations,
    to_datetime,
)
from careeros_job_providers import EmploymentType, JobPosting

_COMMITMENT_TO_TYPE = {
    "full-time": EmploymentType.FULL_TIME,
    "full time": EmploymentType.FULL_TIME,
    "part-time": EmploymentType.PART_TIME,
    "part time": EmploymentType.PART_TIME,
    "contract": EmploymentType.CONTRACT,
    "contractor": EmploymentType.CONTRACT,
    "temporary": EmploymentType.CONTRACT,
    "intern": EmploymentType.INTERNSHIP,
    "internship": EmploymentType.INTERNSHIP,
}


class LeverAdapter(AtsAdapter):
    ats_id = "lever"
    allowed_hosts = frozenset(
        {"api.lever.co", "api.eu.lever.co", "jobs.lever.co", "jobs.eu.lever.co"}
    )

    def fetch_board(self, entry: BoardEntry, http: AtsHttp) -> list[dict[str, Any]]:
        host = "api.eu.lever.co" if entry.extra.get("eu") else "api.lever.co"
        payload = http.get_json(self.check(f"https://{host}/v0/postings/{entry.slug}?mode=json"))
        return [p for p in payload if isinstance(p, dict)] if isinstance(payload, list) else []

    def to_posting(self, raw: dict[str, Any], entry: BoardEntry) -> JobPosting | None:
        url = raw.get("hostedUrl") or raw.get("applyUrl")
        if not url:
            return None
        categories = raw.get("categories") or {}
        location = merge_locations(categories.get("location"), categories.get("allLocations"))
        commitment = (categories.get("commitment") or "").strip().lower()
        description = raw.get("descriptionPlain")
        if not isinstance(description, str) or not description.strip():
            description = html_to_text(raw.get("description"))
        return JobPosting(
            source_provider=self.ats_id,
            external_id=str(raw.get("id") or url),
            title=(raw.get("text") or "").strip(),
            company_name=entry.name,
            url=url,
            # Lever routes the form to a /apply subpath the posting page has no
            # crawlable link to, so deriving it here saves the runner a hop it
            # would otherwise fail to make on a client-rendered page.
            apply_url=raw.get("applyUrl") or f"{url.rstrip('/')}/apply",
            location=location or None,
            remote=looks_remote(location, categories.get("commitment"), raw.get("workplaceType")),
            employment_type=_COMMITMENT_TO_TYPE.get(commitment),
            description=description or "",
            posted_at=to_datetime(raw.get("createdAt")),
        )

    def probe_entry(self) -> BoardEntry:
        # Deliberately a SMALL board. Lever's API returns a whole board with no
        # limit parameter, so probing a large one (Veeva, ~890 roles) blew the
        # registry's 15s health budget once nine ATS providers probed
        # concurrently, and Lever dropped out of every search.
        return BoardEntry("matchgroup", "Match Group")
