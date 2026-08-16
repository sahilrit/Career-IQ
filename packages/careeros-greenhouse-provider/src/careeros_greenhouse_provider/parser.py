"""Normalizes Greenhouse board job entries into JobPosting records."""

from __future__ import annotations

import html
import re
from datetime import datetime
from typing import Any

from careeros_job_providers import EmploymentType, JobPosting

PROVIDER_ID = "greenhouse"

_TAG_RE = re.compile(r"<[^>]+>")
_REMOTE_RE = re.compile(r"\bremote\b", re.IGNORECASE)


def is_job_entry(entry: dict[str, Any]) -> bool:
    return bool(entry.get("id")) and bool(entry.get("title"))


def _strip_html(raw: str) -> str:
    return html.unescape(_TAG_RE.sub(" ", raw or "")).strip()


def _location(entry: dict[str, Any]) -> str | None:
    location = entry.get("location") or {}
    name = location.get("name") if isinstance(location, dict) else None
    return name or None


def _parse_updated_at(entry: dict[str, Any]) -> datetime | None:
    raw = entry.get("updated_at") or entry.get("first_published")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw))
    except ValueError:
        return None


def parse_job_entry(entry: dict[str, Any]) -> JobPosting:
    location = _location(entry)
    description = _strip_html(entry.get("content", ""))
    company = entry.get("company_name") or entry.get("_company") or ""
    remote = bool(location and _REMOTE_RE.search(location)) or bool(
        _REMOTE_RE.search(entry.get("title", ""))
    )
    return JobPosting(
        source_provider=PROVIDER_ID,
        external_id=str(entry["id"]),
        title=(entry.get("title") or "").strip(),
        company_name=str(company).strip().title() if company else "",
        # absolute_url is the Greenhouse-hosted application form (open, no login).
        url=entry.get("absolute_url") or "",
        location=location,
        remote=remote,
        salary=None,
        employment_type=EmploymentType.FULL_TIME,
        description=description,
        tags=[],
        posted_at=_parse_updated_at(entry),
    )
