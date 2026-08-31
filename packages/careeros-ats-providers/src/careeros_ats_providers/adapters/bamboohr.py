"""BambooHR — the public careers JSON each tenant serves at
``<slug>.bamboohr.com/careers/list``.

The list carries no body, and BambooHR's detail endpoint returns the posting
wrapped in a metadata envelope. Detail fetches are bounded like
SmartRecruiters' for the same reason: a whole board would be hundreds of
requests for descriptions most postings will never be scored against.
"""

from __future__ import annotations

from typing import Any

from careeros_ats_providers.adapter import AtsAdapter, BoardEntry
from careeros_ats_providers.http import AtsHttp, BoardFetchError
from careeros_ats_providers.normalize import (
    html_to_text,
    looks_remote,
    merge_locations,
    to_datetime,
)
from careeros_job_providers import JobPosting

DEFAULT_DETAIL_LIMIT = 20


class BambooHrAdapter(AtsAdapter):
    ats_id = "bamboohr"
    allowed_hosts = frozenset({".bamboohr.com"})

    def __init__(self, *, detail_limit: int = DEFAULT_DETAIL_LIMIT) -> None:
        self._detail_limit = max(0, detail_limit)

    def fetch_board(self, entry: BoardEntry, http: AtsHttp) -> list[dict[str, Any]]:
        url = f"https://{entry.slug}.bamboohr.com/careers/list"
        payload = http.get_json(self.check(url))
        result = payload.get("result") if isinstance(payload, dict) else None
        jobs = [j for j in (result or []) if isinstance(j, dict)]
        for job in jobs[: self._detail_limit]:
            job_id = job.get("id")
            if not job_id:
                continue
            detail_url = f"https://{entry.slug}.bamboohr.com/careers/{job_id}/detail"
            try:
                detail = http.get_json(self.check(detail_url))
            except BoardFetchError:
                continue
            if isinstance(detail, dict):
                job["_detail"] = detail.get("result") or detail
        return jobs

    def to_posting(self, raw: dict[str, Any], entry: BoardEntry) -> JobPosting | None:
        job_id = raw.get("id")
        if not job_id:
            return None
        url = f"https://{entry.slug}.bamboohr.com/careers/{job_id}"
        location_block = raw.get("location") or {}
        location = merge_locations(
            location_block.get("city"), location_block.get("state"), location_block.get("country")
        )
        detail = raw.get("_detail") or {}
        job_opening = detail.get("jobOpening") if isinstance(detail, dict) else None
        description = ""
        if isinstance(job_opening, dict):
            description = html_to_text(job_opening.get("description"))
        title = raw.get("jobOpeningName") or raw.get("title") or ""
        return JobPosting(
            source_provider=self.ats_id,
            external_id=str(job_id),
            title=title.strip(),
            company_name=entry.name,
            url=url,
            apply_url=url,
            location=location or None,
            remote=str(raw.get("isRemote") or "").lower() in ("1", "true", "yes")
            or looks_remote(location),
            description=description,
            posted_at=to_datetime(raw.get("datePosted") or raw.get("postedDate")),
        )
