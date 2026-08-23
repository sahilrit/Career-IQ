"""LLM-backed résumé parsing. Heuristic parsing (in careeros-career-brain) is
free and handles clean layouts, but messy PDF text — merged roles, two-column
exports, numeric dates — defeats line-based rules. When the workspace has an AI
key we ask the model to structure the résumé; on any failure the caller falls
back to the heuristic parse, so this never blocks an import."""

from __future__ import annotations

import json
import re
from datetime import date
from typing import Any

from careeros_ai import AIClient
from careeros_career_brain import (
    ParsedCertification,
    ParsedEducation,
    ParsedExperience,
    ParsedResume,
)

_SYSTEM = (
    "You are a precise résumé parser. Extract ONLY facts present in the text — "
    "never invent employers, titles, dates, or metrics. Return strict JSON only."
)

_SHAPE = (
    '{"experiences":[{"title":"","company":"","start":"YYYY-MM",'
    '"end":"YYYY-MM or null if current","description":"the role\'s bullet points, '
    'one per line"}],"education":[{"credential":"","institution":"","end_year":2024}],'
    '"certifications":[{"name":"","issuer":""}],"skills":["",""]}'
)


def _prompt(text: str) -> str:
    return (
        f"Extract this résumé into JSON exactly matching this shape:\n{_SHAPE}\n\n"
        "Rules: keep each role SEPARATE (do not merge roles); put a role's "
        "achievement bullets in its own description, one per line; dates as "
        "YYYY-MM; end=null for a current role; omit anything not present. "
        "Output JSON only, no prose.\n\nRÉSUMÉ:\n" + text[:14000]
    )


def _to_date(value: Any) -> date | None:
    if not value:
        return None
    text = str(value).strip().lower()
    if text in ("present", "current", "now", "null", "none", ""):
        return None
    match = re.match(r"(\d{4})(?:[-/](\d{1,2}))?", text)
    if not match:
        return None
    year = int(match.group(1))
    month = int(match.group(2) or 1)
    return date(year, min(max(month, 1), 12), 1)


def _extract_json(raw: str) -> dict[str, Any] | None:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except (json.JSONDecodeError, ValueError):
        return None


def ai_parse_resume(text: str, client: AIClient) -> ParsedResume | None:
    """Structure a résumé with the LLM. Returns None on any failure so the
    caller can fall back to the heuristic parser."""
    try:
        raw = client.complete(system=_SYSTEM, prompt=_prompt(text))
    except Exception:
        return None
    data = _extract_json(raw)
    if data is None:
        return None
    try:
        experiences = []
        for item in data.get("experiences", [])[:20]:
            title = str(item.get("title", "")).strip()[:120]
            if not title:
                continue
            start = _to_date(item.get("start")) or date(2000, 1, 1)
            end = _to_date(item.get("end"))
            # Never emit an invalid range — drop a nonsensical end instead.
            if end is not None and end < start:
                end = None
            experiences.append(
                ParsedExperience(
                    title=title,
                    company=str(item.get("company", "")).strip()[:120],
                    start_date=start,
                    end_date=end,
                    description=str(item.get("description", "")).strip()[:3000],
                )
            )
        education = [
            ParsedEducation(
                institution=str(item.get("institution", "")).strip()[:120],
                credential=str(item.get("credential", "")).strip()[:160],
                end_date=(date(int(item["end_year"]), 1, 1) if item.get("end_year") else None),
            )
            for item in data.get("education", [])[:10]
            if item.get("credential") or item.get("institution")
        ]
        certifications = [
            ParsedCertification(
                name=str(item.get("name", "")).strip()[:160],
                issuer=(str(item["issuer"]).strip() or None) if item.get("issuer") else None,
            )
            for item in data.get("certifications", [])[:20]
            if item.get("name")
        ]
        skills = [s.strip() for s in data.get("skills", []) if isinstance(s, str) and s.strip()][
            :40
        ]
    except (ValueError, TypeError, KeyError):
        return None

    if not (experiences or education or skills):
        return None
    return ParsedResume(
        experiences=experiences,
        education=education,
        certifications=certifications,
        skills=skills,
    )
