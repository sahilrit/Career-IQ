"""SmartRecruiters — public postings API, no key.

The list endpoint pages at 100 and carries no description; the body lives on
the per-posting detail endpoint. Fetching details for a whole board would be
hundreds of requests, so detail enrichment is bounded (``detail_limit``) and
applied to the first N postings. Everything past that limit keeps an empty
description rather than a fabricated one, and the provider reports how many
were enriched so the truncation is never silent.
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

PAGE_SIZE = 100
MAX_PAGES = 10
DEFAULT_DETAIL_LIMIT = 25


def extract_description(detail: Any) -> str:
    """The posting body, assembled from SmartRecruiters' section blocks."""
    if not isinstance(detail, dict):
        return ""
    sections = ((detail.get("jobAd") or {}).get("sections")) or {}
    if not isinstance(sections, dict):
        return ""
    parts = []
    for key in ("companyDescription", "jobDescription", "qualifications", "additionalInformation"):
        block = sections.get(key)
        text = block.get("text") if isinstance(block, dict) else None
        if isinstance(text, str) and text.strip():
            parts.append(text)
    return html_to_text("\n".join(parts)) if parts else ""


class SmartRecruitersAdapter(AtsAdapter):
    ats_id = "smartrecruiters"
    allowed_hosts = frozenset(
        {"api.smartrecruiters.com", "jobs.smartrecruiters.com", "careers.smartrecruiters.com"}
    )

    def __init__(self, *, detail_limit: int = DEFAULT_DETAIL_LIMIT) -> None:
        self._detail_limit = max(0, detail_limit)

    def fetch_board(self, entry: BoardEntry, http: AtsHttp) -> list[dict[str, Any]]:
        collected: list[dict[str, Any]] = []
        for page in range(MAX_PAGES):
            url = (
                f"https://api.smartrecruiters.com/v1/companies/{entry.slug}/postings"
                f"?limit={PAGE_SIZE}&offset={page * PAGE_SIZE}&status=PUBLIC"
            )
            payload = http.get_json(self.check(url))
            content = payload.get("content") if isinstance(payload, dict) else None
            batch = [p for p in (content or []) if isinstance(p, dict)]
            collected.extend(batch)
            if len(batch) < PAGE_SIZE:
                break

        for posting in collected[: self._detail_limit]:
            posting_id = posting.get("id")
            if not posting_id:
                continue
            detail_url = (
                f"https://api.smartrecruiters.com/v1/companies/{entry.slug}/postings/{posting_id}"
            )
            try:
                posting["_detail"] = http.get_json(self.check(detail_url))
            except BoardFetchError:
                # One unreadable detail must not lose the posting itself - the
                # listing is still applyable, just without a description.
                continue
        return collected

    def probe_board(self, entry: BoardEntry, http: AtsHttp) -> list[dict[str, Any]]:
        # One page, no per-posting detail fetches.
        url = (
            f"https://api.smartrecruiters.com/v1/companies/{entry.slug}/postings"
            "?limit=10&offset=0&status=PUBLIC"
        )
        payload = http.get_json(self.check(url))
        content = payload.get("content") if isinstance(payload, dict) else None
        return [p for p in (content or []) if isinstance(p, dict)]

    def to_posting(self, raw: dict[str, Any], entry: BoardEntry) -> JobPosting | None:
        posting_id = raw.get("id")
        if not posting_id:
            return None
        company = raw.get("company") or {}
        # `identifier` is the tenant slug the careers site is served under and
        # can differ from the slug we crawled with, so prefer it.
        slug = company.get("identifier") or entry.slug
        # Deliberately NOT `ref`: that field is the API's own self-link
        # (api.smartrecruiters.com/v1/...), so using it pointed every posting URL
        # at raw JSON - a page with no form on it, and nothing a human could
        # read either. The careers page is always at this address.
        url = f"https://jobs.smartrecruiters.com/{slug}/{posting_id}"
        location_block = raw.get("location") or {}
        location = merge_locations(
            location_block.get("city"),
            location_block.get("region"),
            location_block.get("country"),
        )
        return JobPosting(
            source_provider=self.ats_id,
            external_id=str(posting_id),
            title=(raw.get("name") or "").strip(),
            company_name=(company.get("name") or entry.name),
            url=url,
            # The posting page, not a guessed subpath. SmartRecruiters routes
            # applications through a `oneclick-ui/company/{slug}/publication/
            # {uuid}` flow whose uuid is not in the postings payload, and whose
            # link text is localised ("Jetzt bewerben"), so it can only be
            # reached by following the link off the posting page.
            apply_url=url,
            location=location or None,
            remote=bool(location_block.get("remote")) or looks_remote(location),
            description=extract_description(raw.get("_detail")),
            posted_at=to_datetime(raw.get("releasedDate") or raw.get("createdOn")),
        )

    def probe_entry(self) -> BoardEntry:
        return BoardEntry("BoschGroup", "Bosch")
