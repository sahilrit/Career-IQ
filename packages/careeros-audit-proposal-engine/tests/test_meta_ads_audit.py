"""Tests for audit_meta_ads / ManualMetaAdsAuditProvider."""

from __future__ import annotations

from careeros_audit_proposal_engine import (
    AdCreative,
    ManualMetaAdsAuditProvider,
    MetaAdsAuditCategory,
    audit_meta_ads,
)


def _strong_ad() -> AdCreative:
    return AdCreative(
        headline="Only here: 20% off, this week only",
        body_text="Unlike other tools, ours ships in a day and saves you real time and money.",
        cta="Shop Now",
        landing_page_url="https://widgetco.example.com/sale",
        destination_is_dedicated_landing_page=True,
    )


def test_no_ads_produces_no_findings():
    assert audit_meta_ads([]) == []


def test_strong_ad_produces_no_findings():
    assert audit_meta_ads([_strong_ad()]) == []


def test_missing_cta_flags_creative():
    ad = _strong_ad().model_copy(update={"cta": ""})
    categories = [f.category for f in audit_meta_ads([ad])]
    assert MetaAdsAuditCategory.CREATIVE.value in categories


def test_thin_copy_flags_messaging():
    ad = _strong_ad().model_copy(update={"body_text": "Buy it."})
    categories = [f.category for f in audit_meta_ads([ad])]
    assert MetaAdsAuditCategory.MESSAGING.value in categories


def test_homepage_destination_flags_landing_page():
    ad = _strong_ad().model_copy(update={"destination_is_dedicated_landing_page": False})
    categories = [f.category for f in audit_meta_ads([ad])]
    assert MetaAdsAuditCategory.LANDING_PAGE.value in categories


def test_no_offer_keywords_flags_offer():
    ad = _strong_ad().model_copy(
        update={"headline": "Our tools", "body_text": "Unlike other tools, ours is better."}
    )
    categories = [f.category for f in audit_meta_ads([ad])]
    assert MetaAdsAuditCategory.OFFER.value in categories


def test_no_differentiation_flags_competitive_positioning():
    ad = _strong_ad().model_copy(
        update={"headline": "20% off this week", "body_text": "Great tools for a great price."}
    )
    categories = [f.category for f in audit_meta_ads([ad])]
    assert MetaAdsAuditCategory.COMPETITIVE_POSITIONING.value in categories


def test_manual_provider_returns_configured_ads(company):
    provider = ManualMetaAdsAuditProvider([_strong_ad()])
    assert provider.collect(company) == [_strong_ad()]
