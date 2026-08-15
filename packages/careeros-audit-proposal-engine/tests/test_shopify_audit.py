"""Tests for ShopifyAuditor."""

from __future__ import annotations

from careeros_audit_proposal_engine import ShopifyAuditCategory, ShopifyAuditor


def _make_clean_storefront(fake_session):
    fake_session.set_query_all_results("meta[name='viewport']", [{"content": "width=device-width"}])
    fake_session.set_visible(".trust-badges")
    fake_session.set_visible(".product-reviews")
    fake_session.set_visible(".announcement-bar")
    fake_session.set_visible(".stock-countdown")
    fake_session.set_visible(".shopify-payment-button")


def test_clean_storefront_has_no_findings(fake_session, company):
    _make_clean_storefront(fake_session)
    assert ShopifyAuditor(fake_session).audit(company) == []


def test_missing_viewport_meta_flags_mobile(fake_session, company):
    fake_session.set_visible(".trust-badges")
    fake_session.set_visible(".product-reviews")
    fake_session.set_visible(".announcement-bar")
    fake_session.set_visible(".stock-countdown")
    fake_session.set_visible(".shopify-payment-button")
    categories = [f.category for f in ShopifyAuditor(fake_session).audit(company)]
    assert ShopifyAuditCategory.MOBILE.value in categories


def test_missing_trust_badges_flags_trust(fake_session, company):
    _make_clean_storefront(fake_session)
    fake_session.set_hidden(".trust-badges")
    categories = [f.category for f in ShopifyAuditor(fake_session).audit(company)]
    assert ShopifyAuditCategory.TRUST.value in categories


def test_missing_reviews_flags_cro(fake_session, company):
    _make_clean_storefront(fake_session)
    fake_session.set_hidden(".product-reviews")
    categories = [f.category for f in ShopifyAuditor(fake_session).audit(company)]
    assert ShopifyAuditCategory.CRO.value in categories


def test_missing_offer_flags_offer(fake_session, company):
    _make_clean_storefront(fake_session)
    fake_session.set_hidden(".announcement-bar")
    categories = [f.category for f in ShopifyAuditor(fake_session).audit(company)]
    assert ShopifyAuditCategory.OFFER.value in categories


def test_missing_urgency_flags_product_page(fake_session, company):
    _make_clean_storefront(fake_session)
    fake_session.set_hidden(".stock-countdown")
    categories = [f.category for f in ShopifyAuditor(fake_session).audit(company)]
    assert ShopifyAuditCategory.PRODUCT_PAGE.value in categories


def test_missing_express_checkout_flags_checkout(fake_session, company):
    _make_clean_storefront(fake_session)
    fake_session.set_hidden(".shopify-payment-button")
    categories = [f.category for f in ShopifyAuditor(fake_session).audit(company)]
    assert ShopifyAuditCategory.CHECKOUT.value in categories


def test_every_finding_has_a_recommendation(fake_session, company):
    findings = ShopifyAuditor(fake_session).audit(company)
    assert all(f.recommendation for f in findings)
