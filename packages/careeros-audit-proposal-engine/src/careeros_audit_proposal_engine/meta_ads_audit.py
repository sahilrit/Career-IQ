"""Meta Ads audit: creative, messaging, funnel/landing page, offer, and
competitive-positioning checks against a set of the prospect's ad
creatives.

There is no free API for pulling a company's live Meta ad creatives —
Meta's Ad Library is public and viewable in a browser, but scraping it
without verified selectors would repeat the mistake Phase 19 explicitly
warned against. ``ManualMetaAdsAuditProvider`` is the zero-cost
reference implementation: it audits ad creatives the caller already has
(e.g. copied by hand from the public Ad Library), the same pattern as
Phase 31's ``ManualCompanyDiscoveryProvider``. A future provider can
plug in a real Ad Library integration behind the same
``MetaAdsAuditProvider`` protocol without this module changing.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel

from careeros_audit_proposal_engine.finding import Finding
from careeros_client_acquisition import Company

_OFFER_KEYWORDS = ("% off", "free", "limited", "sale", "discount", "deal")
_DIFFERENTIATION_KEYWORDS = ("only", "unlike", " vs ", "exclusive", "unlike other")
_MIN_BODY_LENGTH = 30


class MetaAdsAuditCategory(StrEnum):
    CREATIVE = "creative"
    MESSAGING = "messaging"
    LANDING_PAGE = "landing_page"
    OFFER = "offer"
    COMPETITIVE_POSITIONING = "competitive_positioning"


class AdCreative(BaseModel):
    headline: str
    body_text: str
    cta: str = ""
    landing_page_url: str = ""
    destination_is_dedicated_landing_page: bool = True


class MetaAdsAuditProvider(Protocol):
    def collect(self, company: Company) -> list[AdCreative]: ...


class ManualMetaAdsAuditProvider:
    def __init__(self, ads: list[AdCreative]) -> None:
        self._ads = list(ads)

    def collect(self, company: Company) -> list[AdCreative]:
        return list(self._ads)


def audit_meta_ads(ads: list[AdCreative]) -> list[Finding]:
    if not ads:
        return []

    findings: list[Finding] = []

    if any(not ad.cta.strip() for ad in ads):
        findings.append(
            Finding(
                category=MetaAdsAuditCategory.CREATIVE.value,
                detail="at least one ad has no clear call-to-action",
                recommendation="Add an explicit CTA (Shop Now, Get Offer) to every ad creative.",
            )
        )

    if any(len(ad.body_text.strip()) < _MIN_BODY_LENGTH for ad in ads):
        findings.append(
            Finding(
                category=MetaAdsAuditCategory.MESSAGING.value,
                detail="at least one ad's body copy is too thin to communicate real value",
                recommendation="Expand ad copy to state the specific value proposition.",
            )
        )

    if any(not ad.destination_is_dedicated_landing_page for ad in ads):
        findings.append(
            Finding(
                category=MetaAdsAuditCategory.LANDING_PAGE.value,
                detail="at least one ad sends traffic to the homepage instead of a landing page",
                recommendation=(
                    "Build a dedicated landing page matching each ad's offer and message."
                ),
            )
        )

    if not any(_contains_any(ad.headline + " " + ad.body_text, _OFFER_KEYWORDS) for ad in ads):
        findings.append(
            Finding(
                category=MetaAdsAuditCategory.OFFER.value,
                detail="no ad states an explicit offer, discount, or urgency",
                recommendation="Add a concrete, time-bound offer to at least one active ad.",
            )
        )

    if not any(
        _contains_any(ad.headline + " " + ad.body_text, _DIFFERENTIATION_KEYWORDS) for ad in ads
    ):
        findings.append(
            Finding(
                category=MetaAdsAuditCategory.COMPETITIVE_POSITIONING.value,
                detail="no ad differentiates from competitors",
                recommendation="State what makes the offer different from alternatives.",
            )
        )

    return findings


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)
