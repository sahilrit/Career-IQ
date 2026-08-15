"""Extracts interview logistics from an email's free text: date/time,
timezone, platform, meeting link, interviewers, and stage.

No paid NLP service — regex plus python-dateutil's fuzzy parsing (both
free, open-source, local). This is best-effort: real emails vary a lot,
so extracted fields are Optional, and callers should let a human confirm
gaps rather than trusting this blindly for something as consequential as
missing an interview.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

from dateutil import parser as dateutil_parser

from careeros_calendar_assistant.stage import InterviewStage, detect_stage

_TIMEZONE_PATTERNS: dict[str, str] = {
    r"\bEST\b|\bEastern Time\b|\bET\b": "America/New_York",
    r"\bPST\b|\bPacific Time\b|\bPT\b": "America/Los_Angeles",
    r"\bCST\b|\bCentral Time\b|\bCT\b": "America/Chicago",
    r"\bIST\b|\bIndia Standard Time\b": "Asia/Kolkata",
    r"\bBST\b|\bBritish Summer Time\b": "Europe/London",
    r"\bGMT\b": "Etc/GMT",
    r"\bUTC\b": "UTC",
}

_PLATFORM_PATTERNS: dict[str, re.Pattern[str]] = {
    "zoom": re.compile(r"zoom\.us", re.I),
    "google_meet": re.compile(r"meet\.google\.com", re.I),
    "microsoft_teams": re.compile(r"teams\.microsoft\.com|teams\.live\.com", re.I),
    "phone": re.compile(r"\bphone (call|screen)\b|\bwe('| wi)ll call you\b", re.I),
    "onsite": re.compile(r"\bonsite\b|\bin[- ]person\b|\bat our office\b", re.I),
}

_MEETING_LINK_RE = re.compile(
    r"https?://(?:[\w.-]*zoom\.us|meet\.google\.com|teams\.microsoft\.com)[^\s<>)]*", re.I
)

_INTERVIEWER_RE = re.compile(
    r"(?:meeting with|interview(?:ing|ers?)?(?: will be| is| are)?(?: with)?|panel:?)\s+"
    r"((?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)(?:,\s*(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?))*)"
)


@dataclass
class InterviewDetails:
    scheduled_at: datetime | None = None
    timezone: str | None = None
    platform: str | None = None
    meeting_link: str | None = None
    interviewers: list[str] = field(default_factory=list)
    stage: InterviewStage = InterviewStage.UNKNOWN


def _extract_datetime(text: str) -> datetime | None:
    try:
        # ignoretz=True: timezone is extracted separately via
        # _extract_timezone's regex, so dateutil doesn't need to (and
        # otherwise warns when it can't) resolve abbreviations like "EST".
        return dateutil_parser.parse(text, fuzzy=True, ignoretz=True)
    except (ValueError, OverflowError):
        return None


def _extract_timezone(text: str) -> str | None:
    for pattern, iana_name in _TIMEZONE_PATTERNS.items():
        if re.search(pattern, text):
            return iana_name
    return None


def _extract_platform(text: str) -> str | None:
    for platform, pattern in _PLATFORM_PATTERNS.items():
        if pattern.search(text):
            return platform
    return None


def _extract_meeting_link(text: str) -> str | None:
    match = _MEETING_LINK_RE.search(text)
    return match.group(0) if match else None


def _extract_interviewers(text: str) -> list[str]:
    match = _INTERVIEWER_RE.search(text)
    if not match:
        return []
    names = [name.strip() for name in match.group(1).split(",")]
    return [name for name in names if name]


def extract_interview_details(subject: str, body: str) -> InterviewDetails:
    text = f"{subject}\n{body}"
    return InterviewDetails(
        scheduled_at=_extract_datetime(text),
        timezone=_extract_timezone(text),
        platform=_extract_platform(text),
        meeting_link=_extract_meeting_link(text),
        interviewers=_extract_interviewers(text),
        stage=detect_stage(text),
    )
