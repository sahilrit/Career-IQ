"""Recruitee — public offers API, no key. One request per board, bodies included."""

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
from careeros_job_providers import JobPosting


class RecruiteeAdapter(AtsAdapter):
    ats_id = "recruitee"
    allowed_hosts = frozenset({".recruitee.com"})

    def fetch_board(self, entry: BoardEntry, http: AtsHttp) -> list[dict[str, Any]]:
        url = f"https://{entry.slug}.recruitee.com/api/offers/"
        payload = http.get_json(self.check(url))
        offers = payload.get("offers") if isinstance(payload, dict) else None
        return [o for o in (offers or []) if isinstance(o, dict)]

    def to_posting(self, raw: dict[str, Any], entry: BoardEntry) -> JobPosting | None:
        url = raw.get("careers_url") or raw.get("careers_apply_url") or raw.get("url")
        if not url:
            return None
        location = merge_locations(raw.get("city"), raw.get("state_name"), raw.get("country"))
        body = "\n\n".join(
            html_to_text(part)
            for part in (raw.get("description"), raw.get("requirements"))
            if isinstance(part, str)
        ).strip()
        return JobPosting(
            source_provider=self.ats_id,
            external_id=str(raw.get("id") or url),
            title=(raw.get("title") or "").strip(),
            company_name=(raw.get("company_name") or entry.name),
            url=url,
            apply_url=raw.get("careers_apply_url") or url,
            location=location or None,
            remote=bool(raw.get("remote")) or looks_remote(location),
            description=body,
            posted_at=to_datetime(raw.get("published_at") or raw.get("created_at")),
        )

    def probe_entry(self) -> BoardEntry:
        return BoardEntry("channable", "Channable")
