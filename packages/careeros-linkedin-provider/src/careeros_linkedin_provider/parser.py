"""Turn LinkedIn's guest-search HTML into ``JobPosting`` records.

The guest endpoint returns a bare list of ``<li>`` job cards — no page
chrome, no JSON. The markup is regular enough that a targeted
``html.parser`` walk beats pulling in a full DOM library: we only ever
care about six fields, all of them tagged with stable class names.

Everything here is pure: HTML in, plain dicts and models out. The
network lives in ``client.py``.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from html import unescape
from html.parser import HTMLParser
from typing import Any

from careeros_job_providers import JobPosting, Salary

SOURCE_PROVIDER = "linkedin"

# The class names we read off each card. LinkedIn ships several classes per
# element, so these are matched as members of the class list, not equality.
_CARD_CLASS = "base-search-card"
_LINK_CLASS = "base-card__full-link"
_TITLE_CLASS = "base-search-card__title"
_COMPANY_CLASS = "hidden-nested-link"
_LOCATION_CLASS = "job-search-card__location"
_SALARY_CLASS = "job-search-card__salary-info"
# Fresh postings get a "--new" suffix on the same element.
_LISTDATE_CLASS_PREFIX = "job-search-card__listdate"

_JOB_ID_RE = re.compile(r"-(\d{6,})(?:\?|$)")
_URN_RE = re.compile(r"urn:li:jobPosting:(\d+)")
_MONEY_RE = re.compile(r"([£$€₹])?\s*([\d,]+(?:\.\d+)?)\s*([KkMm])?")
_WS_RE = re.compile(r"[ \t\r\f\v]+")
_BLANK_LINES_RE = re.compile(r"\n{3,}")

_CURRENCY_BY_SYMBOL = {"$": "USD", "£": "GBP", "€": "EUR", "₹": "INR"}

_REMOTE_TOKENS = ("remote", "anywhere", "work from home", "worldwide")

# Tags whose boundaries should become line breaks when flattening a job
# description, so the text keeps its paragraph and bullet structure.
_BLOCK_TAGS = {"p", "br", "li", "ul", "ol", "div", "section", "h1", "h2", "h3", "h4", "h5", "h6"}


def _classes(attrs: list[tuple[str, str | None]]) -> set[str]:
    for name, value in attrs:
        if name == "class" and value:
            return set(value.split())
    return set()


def _attr(attrs: list[tuple[str, str | None]], key: str) -> str | None:
    for name, value in attrs:
        if name == key:
            return value
    return None


def _clean(text: str) -> str:
    """LinkedIn pads every text node with newlines and indentation."""
    return " ".join(unescape(text).split())


class _CardParser(HTMLParser):
    """Walks the card list, collecting one dict per ``base-search-card``."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cards: list[dict[str, Any]] = []
        self._card: dict[str, Any] | None = None
        self._depth = 0
        self._capture: str | None = None

    # -- element boundaries -------------------------------------------------
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = _classes(attrs)

        if _CARD_CLASS in classes:
            self._card = {
                "job_id": None,
                "url": None,
                "title": "",
                "company": "",
                "location": "",
                "salary_text": "",
                "posted_at": None,
            }
            self._depth = 0
            urn = _attr(attrs, "data-entity-urn") or ""
            match = _URN_RE.search(urn)
            if match:
                self._card["job_id"] = match.group(1)

        if self._card is None:
            return
        self._depth += 1

        if _LINK_CLASS in classes:
            href = _attr(attrs, "href")
            if href:
                url = unescape(href).split("?", 1)[0]
                self._card["url"] = url
                if not self._card["job_id"]:
                    match = _JOB_ID_RE.search(url)
                    if match:
                        self._card["job_id"] = match.group(1)
        elif _TITLE_CLASS in classes:
            self._capture = "title"
        elif _COMPANY_CLASS in classes:
            self._capture = "company"
        elif _LOCATION_CLASS in classes:
            self._capture = "location"
        elif _SALARY_CLASS in classes:
            self._capture = "salary_text"
        elif any(name.startswith(_LISTDATE_CLASS_PREFIX) for name in classes):
            self._card["posted_at"] = _attr(attrs, "datetime")

    def handle_endtag(self, tag: str) -> None:
        if self._card is None:
            return
        self._capture = None
        self._depth -= 1
        if self._depth <= 0:
            self.cards.append(self._card)
            self._card = None

    def handle_data(self, data: str) -> None:
        if self._card is None or self._capture is None:
            return
        text = _clean(data)
        if not text:
            return
        existing = self._card[self._capture]
        self._card[self._capture] = f"{existing} {text}".strip() if existing else text

    def close(self) -> None:  # pragma: no cover - flushes a truncated document
        super().close()
        if self._card is not None:
            self.cards.append(self._card)
            self._card = None


def extract_job_cards(html: str) -> list[dict[str, Any]]:
    """Every ``base-search-card`` in a guest-search response, as plain dicts.

    Cards missing a link or id are still returned — ``is_job_entry`` is what
    decides whether one is usable, so callers can count and log skips.
    """
    parser = _CardParser()
    parser.feed(html)
    parser.close()
    return parser.cards


def is_job_entry(card: dict[str, Any]) -> bool:
    """A card is usable only if we can identify and link to the posting."""
    return bool(card.get("job_id")) and bool(card.get("url")) and bool(card.get("title"))


def _parse_amount(raw: str, suffix: str | None) -> int | None:
    try:
        value = float(raw.replace(",", ""))
    except ValueError:
        return None
    if suffix and suffix.lower() == "k":
        value *= 1_000
    elif suffix and suffix.lower() == "m":
        value *= 1_000_000
    return int(value)


def parse_salary(text: str) -> Salary | None:
    """LinkedIn's salary strings are free text — ``$120,000 - $150,000``,
    ``£45K/yr``, ``₹8,00,000``. Read what we can and give up quietly."""
    if not text:
        return None
    matches = _MONEY_RE.findall(text)
    amounts = [
        amount
        for symbol, digits, suffix in matches
        if (amount := _parse_amount(digits, suffix)) is not None and amount > 0
    ]
    if not amounts:
        return None

    currency = next(
        (_CURRENCY_BY_SYMBOL[symbol] for symbol, _, _ in matches if symbol in _CURRENCY_BY_SYMBOL),
        "USD",
    )
    period = "hour" if "hr" in text.lower() or "hour" in text.lower() else "year"
    minimum = min(amounts)
    maximum = max(amounts)
    return Salary(
        min_amount=minimum,
        max_amount=maximum if maximum != minimum else None,
        currency=currency,
        period=period,
    )


def _parse_posted_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).replace(tzinfo=UTC)
    except ValueError:
        return None


def is_remote_location(location: str) -> bool:
    lowered = location.lower()
    return any(token in lowered for token in _REMOTE_TOKENS)


def parse_job_entry(card: dict[str, Any], *, description: str = "") -> JobPosting:
    """Map one extracted card onto the shared ``JobPosting`` shape."""
    location = card.get("location") or ""
    return JobPosting(
        source_provider=SOURCE_PROVIDER,
        external_id=str(card["job_id"]),
        title=card.get("title") or "",
        company_name=card.get("company") or "",
        url=card["url"],
        location=location or None,
        remote=is_remote_location(location),
        salary=parse_salary(card.get("salary_text") or ""),
        description=description,
        posted_at=_parse_posted_at(card.get("posted_at")),
    )


class _DescriptionParser(HTMLParser):
    """Flattens the job-view description block into readable plain text."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._depth = 0
        self._inside = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if not self._inside:
            if any(cls.startswith("show-more-less-html__markup") for cls in _classes(attrs)):
                self._inside = True
                self._depth = 1
            return
        self._depth += 1
        if tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if not self._inside:
            return
        if tag in _BLOCK_TAGS:
            self.parts.append("\n")
        self._depth -= 1
        if self._depth <= 0:
            self._inside = False

    def handle_data(self, data: str) -> None:
        if self._inside:
            self.parts.append(data)


def parse_description_html(html: str) -> str:
    """The job description as plain text, or ``""`` when the block is absent.

    ``&nbsp;`` arrives as U+00A0 after charref conversion; collapsing it into
    an ordinary space matters because the scorer tokenizes this text.
    """
    parser = _DescriptionParser()
    parser.feed(html)
    parser.close()
    if not parser.parts:
        return ""
    text = unescape("".join(parser.parts)).replace("\N{NO-BREAK SPACE}", " ")
    text = _WS_RE.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    return _BLANK_LINES_RE.sub("\n\n", text).strip()
