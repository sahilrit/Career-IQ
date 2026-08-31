"""Turning whatever an ATS returns into the shapes the rest of CareerOS uses.

Two jobs here that every adapter needs and none should reimplement:

* **HTML to plain text.** Board APIs return descriptions as HTML, and some
  (Greenhouse) return it *double-encoded* — the JSON string carries
  entity-escaped markup, so the entities must be decoded before the tags can
  be stripped, and text-level entities only become decodable once the tags are
  gone. Getting this order wrong leaves `&lt;p&gt;` in the description, which
  then poisons keyword scoring. (Behaviour verified against career-ops, MIT,
  which documents the same double-encoding.)
* **Salary normalization.** Ashby quotes compensation per interval (hourly,
  monthly); comparing a monthly figure against an annual expectation silently
  mis-scores every one of those postings.
"""

from __future__ import annotations

import html
import re
from datetime import UTC, datetime

from careeros_job_providers import Salary

_TAG_RE = re.compile(r"<[^>]+>")
_BLOCK_END_RE = re.compile(r"</(p|div|li|ul|ol|h[1-6]|tr|br)\s*/?>", re.I)
_BR_RE = re.compile(r"<br\s*/?>", re.I)
_WS_RE = re.compile(r"[ \t]+")
_BLANKS_RE = re.compile(r"\n{3,}")


def html_to_text(content: object) -> str:
    """Entity-decoded, tag-stripped plain text. Empty string for non-strings.

    Decodes entities BEFORE stripping tags so double-encoded markup
    (``&lt;p&gt;Hello&lt;/p&gt;``) becomes real tags that then get stripped,
    rather than being left as visible angle-bracket noise in the description.
    """
    if not isinstance(content, str) or not content.strip():
        return ""
    text = html.unescape(content)
    # A second pass: the first unescape may itself have revealed entities that
    # were escaped twice. Cheap, and it is the difference between "R&amp;D" and
    # "R&D" in a description a human reads.
    if "&" in text:
        text = html.unescape(text)
    text = _BR_RE.sub("\n", text)
    text = _BLOCK_END_RE.sub("\n", text)
    text = _TAG_RE.sub("", text)
    text = _WS_RE.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    return _BLANKS_RE.sub("\n\n", text).strip()


def to_datetime(value: object) -> datetime | None:
    """A posting date from an ISO string or epoch (seconds or milliseconds)."""
    if value is None or value == "":
        return None
    if isinstance(value, int | float):
        # Lever returns epoch MILLISECONDS. Treating those as seconds puts every
        # posting ~50,000 years in the future, which breaks recency filtering.
        seconds = value / 1000 if value > 10_000_000_000 else value
        try:
            return datetime.fromtimestamp(seconds, tz=UTC)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        raw = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return None


#: Interval -> how many of them make a year. Used to bring every quoted
#: compensation onto the annual basis the rest of CareerOS compares against.
_INTERVAL_TO_ANNUAL: dict[str, float] = {
    "1 HOUR": 2080,
    "HOURLY": 2080,
    "1 DAY": 260,
    "DAILY": 260,
    "1 WEEK": 52,
    "WEEKLY": 52,
    "2 WEEK": 26,
    "BIWEEKLY": 26,
    "0.5 MONTH": 24,
    "SEMIMONTHLY": 24,
    "1 MONTH": 12,
    "MONTHLY": 12,
    "2 MONTH": 6,
    "3 MONTH": 4,
    "QUARTERLY": 4,
    "6 MONTH": 2,
    "1 YEAR": 1,
    "YEARLY": 1,
    "ANNUAL": 1,
}


def _number(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def annualized_salary(
    min_value: object, max_value: object, currency: object, interval: object
) -> Salary | None:
    """A Salary normalized to an annual figure, or None when there is no signal.

    Returns None rather than a zero/partial Salary: an absent salary and a
    salary of nothing must stay distinguishable, because scoring treats them
    completely differently.
    """
    multiplier = _INTERVAL_TO_ANNUAL.get(str(interval or "1 YEAR").strip().upper())
    if multiplier is None:
        return None
    low = _number(min_value)
    high = _number(max_value)
    if low is None and high is None:
        return None
    low = low if low is not None else high
    high = high if high is not None else low
    annual_low = int(min(low, high) * multiplier)
    annual_high = int(max(low, high) * multiplier)
    code = str(currency or "USD").strip().upper() or "USD"
    return Salary(min_amount=annual_low, max_amount=annual_high, currency=code, period="year")


_REMOTE_RE = re.compile(r"\bremote\b|\bwork from home\b|\bdistributed\b|\banywhere\b", re.I)
#: "Remote" inside these phrases means the opposite of remote-friendly.
_NOT_REMOTE_RE = re.compile(r"\bnot remote\b|\bno remote\b|\bon-?site only\b|\bhybrid\b", re.I)


def looks_remote(*fields: object) -> bool:
    """Whether any of the given strings indicates a remote role."""
    for field in fields:
        if not isinstance(field, str) or not field:
            continue
        if _NOT_REMOTE_RE.search(field):
            continue
        if _REMOTE_RE.search(field):
            return True
    return False


def merge_locations(*values: object) -> str:
    """Distinct, order-preserving location strings joined for display.

    Boards routinely put the work model ("Hybrid") in the primary location and
    the actual city somewhere else; keeping both is what lets a location filter
    see a city at all.
    """
    merged: list[str] = []
    for value in values:
        candidates: list[str] = []
        if isinstance(value, str):
            candidates = [value]
        elif isinstance(value, list | tuple):
            candidates = [v for v in value if isinstance(v, str)]
        for candidate in candidates:
            text = candidate.strip()
            if text and not any(text.lower() == existing.lower() for existing in merged):
                merged.append(text)
    return "; ".join(merged)
