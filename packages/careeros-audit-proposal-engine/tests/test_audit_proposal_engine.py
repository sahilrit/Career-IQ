"""Tests for the AuditProposalEngine facade."""

from __future__ import annotations

from careeros_audit_proposal_engine import (
    AdCreative,
    AuditProposalEngine,
    ManualMetaAdsAuditProvider,
    ROIInputs,
    ShopifyAuditor,
    from_baseline_finding,
)
from careeros_client_acquisition import AuditFinding as BaselineAuditFinding
from careeros_client_acquisition import SignalType


def test_from_baseline_finding_adapts_signal_type_as_category():
    baseline = BaselineAuditFinding(
        signal_type=SignalType.NO_HTTPS, detail="http://x", recommendation="Move to HTTPS."
    )
    finding = from_baseline_finding(baseline)
    assert finding.category == "no_https"
    assert finding.detail == "http://x"


def test_collect_findings_merges_baseline_and_shopify(fake_session, company):
    fake_session.set_query_all_results("meta[name='viewport']", [{"content": "width=device-width"}])
    fake_session.set_visible(".trust-badges")
    fake_session.set_visible(".product-reviews")
    fake_session.set_visible(".announcement-bar")
    fake_session.set_visible(".stock-countdown")
    # leave express checkout unset -> 1 shopify finding expected

    baseline = [
        BaselineAuditFinding(
            signal_type=SignalType.NO_HTTPS, detail="http://x", recommendation="Move to HTTPS."
        )
    ]
    engine = AuditProposalEngine(shopify_auditor=ShopifyAuditor(fake_session))
    findings = engine.collect_findings(company, baseline)

    assert len(findings) == 2
    assert {f.category for f in findings} == {"no_https", "checkout"}


def test_collect_findings_includes_meta_ads_when_provider_given(company):
    thin_ad = AdCreative(headline="Hi", body_text="Buy it.", cta="")
    engine = AuditProposalEngine(meta_ads_provider=ManualMetaAdsAuditProvider([thin_ad]))
    findings = engine.collect_findings(company)
    assert len(findings) > 0


def test_generate_deliverables_produces_every_output(brain, company, tmp_path):
    engine = AuditProposalEngine()
    findings = engine.collect_findings(company)
    deliverables = engine.generate_deliverables(
        brain,
        company,
        findings,
        roi_inputs=ROIInputs(
            monthly_visitors=10_000, conversion_rate=0.02, average_order_value=50.0
        ),
        pdf_output_path=tmp_path / "audit.pdf",
    )

    assert deliverables.roi_estimate is not None
    assert company.name in deliverables.loom_script
    assert company.name in deliverables.email
    assert company.name in deliverables.linkedin_message
    assert company.name in deliverables.proposal
    assert deliverables.pdf_path.exists()


def test_generate_deliverables_without_roi_inputs_has_no_roi_estimate(brain, company, tmp_path):
    engine = AuditProposalEngine()
    deliverables = engine.generate_deliverables(
        brain, company, [], pdf_output_path=tmp_path / "audit.pdf"
    )
    assert deliverables.roi_estimate is None
