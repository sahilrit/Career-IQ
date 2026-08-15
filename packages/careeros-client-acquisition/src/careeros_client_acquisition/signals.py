"""Problem-signal detection: what's actually wrong with a prospective
client's website, observed directly rather than guessed. Every signal
here is something the detector actually read off the page — nothing is
inferred or fabricated.

The selectors below are documented starting points, not guaranteed-
correct production values (same caveat as careeros-fiverr-provider's
default selectors, Phase 19) — real sites vary, and a production
deployment should tune ``WebsiteSignalRules`` to what it actually finds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from pydantic import BaseModel

from careeros_browser import BrowserSession
from careeros_client_acquisition.company import Company


class SignalType(StrEnum):
    NO_HTTPS = "no_https"
    MISSING_META_DESCRIPTION = "missing_meta_description"
    NO_TESTIMONIALS = "no_testimonials"
    NO_LIVE_CHAT = "no_live_chat"
    THIN_HOMEPAGE_CONTENT = "thin_homepage_content"


class ProblemSignal(BaseModel):
    signal_type: SignalType
    detail: str


@dataclass(frozen=True)
class WebsiteSignalRules:
    testimonial_selectors: list[str] = field(
        default_factory=lambda: [".testimonial", ".reviews", ".testimonials"]
    )
    live_chat_selectors: list[str] = field(
        default_factory=lambda: ["#chat-widget", ".intercom-launcher", ".crisp-client"]
    )
    meta_description_selector: str = "meta[name='description']"
    body_selector: str = "body"
    min_content_length: int = 200


class WebsiteSignalDetector:
    def __init__(self, session: BrowserSession, rules: WebsiteSignalRules | None = None) -> None:
        self._session = session
        self._rules = rules or WebsiteSignalRules()

    def detect(self, company: Company) -> list[ProblemSignal]:
        self._session.goto(company.website)
        signals: list[ProblemSignal] = []

        if not self._session.current_url.lower().startswith("https://"):
            signals.append(
                ProblemSignal(signal_type=SignalType.NO_HTTPS, detail=self._session.current_url)
            )

        meta = self._session.query_all(
            self._rules.meta_description_selector, extract={"content": "@content"}
        )
        if not meta or not (meta[0].get("content") or "").strip():
            signals.append(
                ProblemSignal(
                    signal_type=SignalType.MISSING_META_DESCRIPTION,
                    detail="no meta description tag found",
                )
            )

        if not any(self._session.is_visible(sel) for sel in self._rules.testimonial_selectors):
            signals.append(
                ProblemSignal(
                    signal_type=SignalType.NO_TESTIMONIALS,
                    detail="no testimonials/reviews section visible",
                )
            )

        if not any(self._session.is_visible(sel) for sel in self._rules.live_chat_selectors):
            signals.append(
                ProblemSignal(
                    signal_type=SignalType.NO_LIVE_CHAT, detail="no live chat widget visible"
                )
            )

        body_text = self._session.text_content(self._rules.body_selector) or ""
        if len(body_text.strip()) < self._rules.min_content_length:
            signals.append(
                ProblemSignal(
                    signal_type=SignalType.THIN_HOMEPAGE_CONTENT,
                    detail=f"homepage body is only {len(body_text.strip())} characters",
                )
            )

        return signals
