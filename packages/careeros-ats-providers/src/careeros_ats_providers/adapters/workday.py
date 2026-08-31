"""Workday — the CXS search API behind every ``*.myworkdayjobs.com`` site.

Workday is the least uniform of the hosted ATSes and the most important to get
honest about:

* Every customer is a separate TENANT with its own host and its own site
  identifier, so a board entry needs three parts (``tenant``, ``site``, and
  the host's region prefix) rather than one slug. There is no global index of
  them — a Workday board has to be added deliberately.
* The API is a POST with a JSON body and returns 20 per page.
* The rendered posting page is a virtualized React app whose body a scraper
  cannot see; the CXS endpoint is the only reliable read. (career-ops
  documents the same conclusion.)

Descriptions come from the per-posting CXS detail endpoint and are bounded,
like the other paged adapters.
"""

from __future__ import annotations

from typing import Any

from careeros_ats_providers.adapter import AtsAdapter, BoardEntry
from careeros_ats_providers.http import AtsHttp, BoardFetchError
from careeros_ats_providers.normalize import html_to_text, looks_remote, to_datetime
from careeros_job_providers import JobPosting

PAGE_SIZE = 20
MAX_PAGES = 5
DEFAULT_DETAIL_LIMIT = 15


class WorkdayAdapter(AtsAdapter):
    ats_id = "workday"
    allowed_hosts = frozenset({".myworkdayjobs.com", ".myworkdaysite.com"})

    def __init__(self, *, detail_limit: int = DEFAULT_DETAIL_LIMIT) -> None:
        self._detail_limit = max(0, detail_limit)

    @staticmethod
    def _host(entry: BoardEntry) -> str:
        # Tenants live on a regional host: wd1, wd3, wd5... It is part of the
        # board entry because it cannot be derived from the tenant name.
        region = entry.extra.get("region", "wd1")
        return f"{entry.slug}.{region}.myworkdayjobs.com"

    def _cxs_base(self, entry: BoardEntry) -> str:
        site = entry.extra.get("site") or "External"
        return f"https://{self._host(entry)}/wday/cxs/{entry.slug}/{site}"

    def fetch_board(self, entry: BoardEntry, http: AtsHttp) -> list[dict[str, Any]]:
        base = self._cxs_base(entry)
        collected: list[dict[str, Any]] = []
        for page in range(MAX_PAGES):
            body = {
                "appliedFacets": {},
                "limit": PAGE_SIZE,
                "offset": page * PAGE_SIZE,
                "searchText": entry.extra.get("search", ""),
            }
            payload = http.post_json(
                self.check(f"{base}/jobs"), body, headers={"Content-Type": "application/json"}
            )
            postings = payload.get("jobPostings") if isinstance(payload, dict) else None
            batch = [p for p in (postings or []) if isinstance(p, dict)]
            collected.extend(batch)
            if len(batch) < PAGE_SIZE:
                break

        for posting in collected[: self._detail_limit]:
            path = posting.get("externalPath")
            if not isinstance(path, str) or not path:
                continue
            try:
                detail = http.get_json(self.check(f"{base}{path}"))
            except BoardFetchError:
                continue
            if isinstance(detail, dict):
                posting["_detail"] = detail.get("jobPostingInfo") or {}
        return collected

    def to_posting(self, raw: dict[str, Any], entry: BoardEntry) -> JobPosting | None:
        path = raw.get("externalPath")
        if not isinstance(path, str) or not path:
            return None
        site = entry.extra.get("site") or "External"
        url = f"https://{self._host(entry)}/{site}{path}"
        detail = raw.get("_detail") or {}
        location = raw.get("locationsText") or detail.get("location") or ""
        return JobPosting(
            source_provider=self.ats_id,
            external_id=str(
                raw.get("bulletFields", [path])[0] if raw.get("bulletFields") else path
            ),
            title=(raw.get("title") or "").strip(),
            company_name=entry.name,
            url=url,
            apply_url=detail.get("externalUrl") or url,
            location=location or None,
            remote=bool(detail.get("remoteType")) or looks_remote(location, raw.get("title")),
            description=html_to_text(detail.get("jobDescription")),
            posted_at=to_datetime(detail.get("startDate") or raw.get("postedOn")),
        )
