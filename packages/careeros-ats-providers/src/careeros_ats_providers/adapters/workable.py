"""Workable — the public account widget behind apply.workable.com.

``?details=true`` returns each posting with its description, so a board is one
request. Workable rate-limits more aggressively than the other hosted boards
and expects a browser-shaped request, so it gets an explicit Accept/Origin.
"""

from __future__ import annotations

import re
from typing import Any

from careeros_ats_providers.adapter import AtsAdapter, BoardEntry
from careeros_ats_providers.http import AtsHttp
from careeros_ats_providers.normalize import (
    html_to_text,
    looks_remote,
    merge_locations,
    to_datetime,
)
from careeros_job_providers import JobPosting

SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


class WorkableAdapter(AtsAdapter):
    ats_id = "workable"
    allowed_hosts = frozenset({"apply.workable.com"})

    def fetch_board(self, entry: BoardEntry, http: AtsHttp) -> list[dict[str, Any]]:
        if not SLUG_RE.match(entry.slug):
            return []
        url = f"https://apply.workable.com/api/v1/widget/accounts/{entry.slug}?details=true"
        payload = http.get_json(
            self.check(url),
            headers={"Origin": "https://apply.workable.com", "Accept-Language": "en-US,en;q=0.9"},
        )
        jobs = payload.get("jobs") if isinstance(payload, dict) else None
        return [j for j in (jobs or []) if isinstance(j, dict)]

    def to_posting(self, raw: dict[str, Any], entry: BoardEntry) -> JobPosting | None:
        url = raw.get("url") or raw.get("shortlink") or raw.get("application_url")
        if not url:
            return None
        location = merge_locations(
            raw.get("city"), raw.get("state"), raw.get("country"), raw.get("location")
        )
        return JobPosting(
            source_provider=self.ats_id,
            external_id=str(raw.get("shortcode") or raw.get("id") or url),
            title=(raw.get("title") or "").strip(),
            company_name=(raw.get("company") or entry.name),
            url=url,
            apply_url=raw.get("application_url") or url,
            location=location or None,
            remote=bool(raw.get("telecommuting")) or looks_remote(location),
            description=html_to_text(raw.get("description")),
            posted_at=to_datetime(raw.get("published_on") or raw.get("created_at")),
        )

    def probe_entry(self) -> BoardEntry:
        return BoardEntry("blueground", "Blueground")
