"""Greenhouse — public boards API, no key.

Two details matter and both were learned from real boards rather than docs:

* ``content=true`` embeds each posting's body in the LIST response, so a whole
  board costs one request instead of one-per-job. Without it every posting
  arrives with an empty description and keyword scoring runs blind.
* Some boards put the *work model* ("Hybrid", "Distributed") in
  ``location.name`` and keep the actual city in a separate ``/offices``
  document. For those boards a location filter never sees a city and drops
  every role. The city is recovered with one extra request, made only for
  boards that actually show the pattern — a board already reporting real
  cities pays nothing. (Both behaviours are documented in career-ops, MIT.)
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

_WORK_MODEL_RE = re.compile(
    r"^(?:hybrid|in[-\s]?office|on[-\s]?site|distributed|remote|flexible)$", re.I
)


def is_work_model_only(name: object) -> bool:
    """True when a location says only how you work, never where.

    "Hybrid" and "Distributed; Hybrid" qualify; "Hybrid - London" does not,
    because that one already contains a filterable place and must be left
    alone — enrichment can never rewrite a location that was working.
    """
    if not isinstance(name, str):
        return False
    parts = [p.strip() for p in name.split(";") if p.strip()]
    return bool(parts) and all(_WORK_MODEL_RE.match(p) for p in parts)


def build_office_map(payload: Any) -> dict[Any, list[str]]:
    """job id -> office names, by walking offices → departments → jobs.

    A job listed under several offices keeps all of them, which is how a
    genuinely multi-site role keeps every city it is open to.
    """
    found: dict[Any, list[str]] = {}

    def walk(offices: Any) -> None:
        if not isinstance(offices, list):
            return
        for office in offices:
            if not isinstance(office, dict):
                continue
            name = (office.get("name") or "").strip() if isinstance(office.get("name"), str) else ""
            if name:
                for dept in office.get("departments") or []:
                    if not isinstance(dept, dict):
                        continue
                    for job in dept.get("jobs") or []:
                        if not isinstance(job, dict) or job.get("id") is None:
                            continue
                        names = found.setdefault(job["id"], [])
                        if name not in names:
                            names.append(name)
            walk(office.get("children"))

    walk((payload or {}).get("offices") if isinstance(payload, dict) else None)
    return found


class GreenhouseAdapter(AtsAdapter):
    ats_id = "greenhouse"
    allowed_hosts = frozenset(
        {
            "boards-api.greenhouse.io",
            "boards.greenhouse.io",
            "job-boards.greenhouse.io",
            "job-boards.eu.greenhouse.io",
            "api.greenhouse.io",
        }
    )

    def _jobs_url(self, slug: str) -> str:
        return f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"

    def _offices_url(self, slug: str) -> str:
        return f"https://boards-api.greenhouse.io/v1/boards/{slug}/offices"

    def fetch_board(self, entry: BoardEntry, http: AtsHttp) -> list[dict[str, Any]]:
        payload = http.get_json(self.check(self._jobs_url(entry.slug)))
        jobs = payload.get("jobs") if isinstance(payload, dict) else None
        usable = [j for j in (jobs or []) if isinstance(j, dict) and j.get("absolute_url")]

        # Only pay for /offices when this board actually hides its cities there.
        if any(is_work_model_only((j.get("location") or {}).get("name")) for j in usable):
            try:
                offices = build_office_map(http.get_json(self.check(self._offices_url(entry.slug))))
            except Exception:
                # Best-effort: a board with no /offices is normal and harmless.
                # A scan must never fail because a secondary lookup did.
                offices = {}
            for job in usable:
                location = (job.get("location") or {}).get("name")
                if is_work_model_only(location) and job.get("id") in offices:
                    job["_offices"] = offices[job["id"]]
        return usable

    def probe_board(self, entry: BoardEntry, http: AtsHttp) -> list[dict[str, Any]]:
        # No content=true and no /offices enrichment: a health check only needs
        # to know the board answers with postings. The full Stripe board with
        # bodies is several MB and does not fit a health-check timeout.
        url = f"https://boards-api.greenhouse.io/v1/boards/{entry.slug}/jobs"
        payload = http.get_json(self.check(url))
        jobs = payload.get("jobs") if isinstance(payload, dict) else None
        return [j for j in (jobs or []) if isinstance(j, dict)]

    def to_posting(self, raw: dict[str, Any], entry: BoardEntry) -> JobPosting | None:
        url = raw.get("absolute_url")
        if not url:
            return None
        description = html_to_text(raw.get("content"))
        location = merge_locations((raw.get("location") or {}).get("name"), raw.get("_offices"))
        # `absolute_url` is whatever the board is configured to point at, and
        # for large customers that is usually their OWN careers site
        # (stripe.com, careers.airbnb.com), not a hosted form. The
        # Greenhouse-hosted form, when one exists, is always at this canonical
        # address — so prefer it and let a self-hosting employer redirect away
        # from it, which the runner then reports honestly. Verified live: Figma
        # and Reddit serve the real form here while their absolute_url does not.
        job_id = raw.get("id")
        apply_url = (
            f"https://job-boards.greenhouse.io/{entry.slug}/jobs/{job_id}" if job_id else url
        )
        return JobPosting(
            source_provider=self.ats_id,
            external_id=str(job_id or url),
            title=(raw.get("title") or "").strip(),
            company_name=entry.name,
            url=url,
            apply_url=apply_url,
            location=location or None,
            remote=looks_remote(location, raw.get("title")),
            description=description,
            posted_at=to_datetime(raw.get("first_published") or raw.get("updated_at")),
        )

    def probe_entry(self) -> BoardEntry:
        return BoardEntry("stripe", "Stripe")
