"""Shopify storefront audit: UX, CRO, product page, checkout, offer,
pricing, trust, and mobile signals read directly off the public
storefront — no Shopify Partner API access required. Same caveat as
Phase 31's WebsiteSignalDetector: the default selectors are documented
starting points, not guaranteed-correct production values.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from careeros_audit_proposal_engine.finding import Finding
from careeros_browser import BrowserSession
from careeros_client_acquisition import Company


class ShopifyAuditCategory(StrEnum):
    UX = "ux"
    CRO = "cro"
    PRODUCT_PAGE = "product_page"
    CHECKOUT = "checkout"
    OFFER = "offer"
    PRICING = "pricing"
    TRUST = "trust"
    MOBILE = "mobile"


_RECOMMENDATIONS: dict[ShopifyAuditCategory, str] = {
    ShopifyAuditCategory.MOBILE: (
        "Add a responsive viewport meta tag — mobile traffic is most of Shopify's."
    ),
    ShopifyAuditCategory.TRUST: (
        "Add trust badges (secure checkout, payment icons) near the buy button."
    ),
    ShopifyAuditCategory.CRO: (
        "Add a reviews/ratings widget on product pages — social proof lifts add-to-cart rate."
    ),
    ShopifyAuditCategory.OFFER: (
        "Surface an active offer or discount — an unadvertised promo converts nobody."
    ),
    ShopifyAuditCategory.PRODUCT_PAGE: (
        "Add product page urgency/scarcity messaging (stock level, sale countdown)."
    ),
    ShopifyAuditCategory.CHECKOUT: ("Add an express/one-click checkout option to cut abandonment."),
}


@dataclass(frozen=True)
class ShopifyStorefrontRules:
    viewport_meta_selector: str = "meta[name='viewport']"
    trust_badge_selectors: list[str] = field(
        default_factory=lambda: [".trust-badges", ".payment-icons", ".security-badge"]
    )
    reviews_selectors: list[str] = field(
        default_factory=lambda: [".product-reviews", ".shopify-product-reviews", ".spr-container"]
    )
    offer_selectors: list[str] = field(
        default_factory=lambda: [".announcement-bar", ".discount-banner", ".promo-bar"]
    )
    urgency_selectors: list[str] = field(
        default_factory=lambda: [".stock-countdown", ".low-stock", ".sale-countdown"]
    )
    express_checkout_selectors: list[str] = field(
        default_factory=lambda: [".shopify-payment-button", ".additional-checkout-buttons"]
    )


class ShopifyAuditor:
    def __init__(
        self, session: BrowserSession, rules: ShopifyStorefrontRules | None = None
    ) -> None:
        self._session = session
        self._rules = rules or ShopifyStorefrontRules()

    def audit(self, company: Company) -> list[Finding]:
        self._session.goto(company.website)
        findings: list[Finding] = []

        meta = self._session.query_all(
            self._rules.viewport_meta_selector, extract={"content": "@content"}
        )
        if not meta or not (meta[0].get("content") or "").strip():
            findings.append(self._finding(ShopifyAuditCategory.MOBILE, "no viewport meta tag"))

        if not any(self._session.is_visible(sel) for sel in self._rules.trust_badge_selectors):
            findings.append(self._finding(ShopifyAuditCategory.TRUST, "no trust badges visible"))

        if not any(self._session.is_visible(sel) for sel in self._rules.reviews_selectors):
            findings.append(
                self._finding(ShopifyAuditCategory.CRO, "no product reviews widget visible")
            )

        if not any(self._session.is_visible(sel) for sel in self._rules.offer_selectors):
            findings.append(self._finding(ShopifyAuditCategory.OFFER, "no active offer visible"))

        if not any(self._session.is_visible(sel) for sel in self._rules.urgency_selectors):
            findings.append(
                self._finding(ShopifyAuditCategory.PRODUCT_PAGE, "no urgency/scarcity messaging")
            )

        if not any(self._session.is_visible(sel) for sel in self._rules.express_checkout_selectors):
            findings.append(
                self._finding(ShopifyAuditCategory.CHECKOUT, "no express checkout option visible")
            )

        return findings

    def _finding(self, category: ShopifyAuditCategory, detail: str) -> Finding:
        return Finding(
            category=category.value, detail=detail, recommendation=_RECOMMENDATIONS[category]
        )
