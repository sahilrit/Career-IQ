"""Personio — the public XML job feed each tenant serves.

Personio is the one adapter here with no JSON API: its public surface is an
XML feed. Parsed with the stdlib, and deliberately with entity resolution left
at defaults-off behaviour by using ElementTree, which does not expand external
entities — an XXE guard that matters because the feed host is derived from a
company slug.
"""

from __future__ import annotations

from typing import Any
from xml.etree import ElementTree

from careeros_ats_providers.adapter import AtsAdapter, BoardEntry
from careeros_ats_providers.http import AtsHttp, BoardFetchError
from careeros_ats_providers.normalize import (
    html_to_text,
    looks_remote,
    merge_locations,
    to_datetime,
)
from careeros_job_providers import JobPosting


def _text(node: Any, *names: str) -> str:
    for name in names:
        found = node.find(name)
        if found is not None and (found.text or "").strip():
            return found.text.strip()
    return ""


class PersonioAdapter(AtsAdapter):
    ats_id = "personio"
    allowed_hosts = frozenset({".jobs.personio.com", ".jobs.personio.de"})

    def fetch_board(self, entry: BoardEntry, http: AtsHttp) -> list[dict[str, Any]]:
        url = f"https://{entry.slug}.jobs.personio.com/xml"
        raw = http.get_text(self.check(url))
        try:
            root = ElementTree.fromstring(raw)
        except ElementTree.ParseError as exc:
            raise BoardFetchError(f"personio: {entry.slug} feed is not valid XML: {exc}") from exc
        positions = []
        for node in root.iter("position"):
            descriptions = " ".join(
                (child.text or "") for child in node.iter("value") if child.text
            )
            positions.append(
                {
                    "id": _text(node, "id"),
                    "title": _text(node, "name"),
                    "office": _text(node, "office"),
                    "department": _text(node, "department"),
                    "schedule": _text(node, "schedule"),
                    "created": _text(node, "createdAt", "occupation"),
                    "description": descriptions,
                }
            )
        return positions

    def to_posting(self, raw: dict[str, Any], entry: BoardEntry) -> JobPosting | None:
        job_id = raw.get("id")
        if not job_id:
            return None
        url = f"https://{entry.slug}.jobs.personio.com/job/{job_id}"
        location = merge_locations(raw.get("office"))
        return JobPosting(
            source_provider=self.ats_id,
            external_id=str(job_id),
            title=(raw.get("title") or "").strip(),
            company_name=entry.name,
            url=url,
            apply_url=f"{url}#apply",
            location=location or None,
            remote=looks_remote(location, raw.get("schedule")),
            description=html_to_text(raw.get("description")),
            posted_at=to_datetime(raw.get("created")),
        )
