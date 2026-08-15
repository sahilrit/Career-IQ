"""Tests for deliverable generation (Loom script, email, LinkedIn, proposal, PDF)."""

from __future__ import annotations

from careeros_audit_proposal_engine import (
    Finding,
    ROIInputs,
    estimate_roi,
    generate_audit_pdf,
    render_audit_email,
    render_linkedin_message,
    render_loom_script,
    render_proposal,
)


def _finding() -> Finding:
    return Finding(category="trust", detail="no trust badges visible", recommendation="Add badges.")


def test_loom_script_mentions_company_and_finding(company):
    script = render_loom_script(company, [_finding()])
    assert company.name in script
    assert "no trust badges visible" in script


def test_audit_email_mentions_findings_and_sender(brain, company):
    email = render_audit_email(brain, company, [_finding()], None)
    assert "no trust badges visible" in email
    assert brain.identity.full_name in email


def test_audit_email_includes_roi_when_provided(brain, company):
    inputs = ROIInputs(monthly_visitors=10_000, conversion_rate=0.02, average_order_value=50.0)
    roi = estimate_roi(inputs, 1)
    email = render_audit_email(brain, company, [_finding()], roi)
    assert "$" in email


def test_linkedin_message_stays_within_length_limit(company):
    message = render_linkedin_message(company, [_finding()])
    assert len(message) <= 300


def test_linkedin_message_with_no_findings_still_generates(company):
    message = render_linkedin_message(company, [])
    assert company.name in message


def test_proposal_includes_findings_and_signature(brain, company):
    proposal = render_proposal(brain, company, [_finding()])
    assert "no trust badges visible" in proposal
    assert brain.identity.full_name in proposal


def test_proposal_includes_roi_when_provided(brain, company):
    inputs = ROIInputs(monthly_visitors=10_000, conversion_rate=0.02, average_order_value=50.0)
    roi = estimate_roi(inputs, 1)
    proposal = render_proposal(brain, company, [_finding()], roi)
    assert "Projected impact" in proposal


def test_generate_audit_pdf_writes_a_real_pdf_file(company, tmp_path):
    output_path = tmp_path / "audit.pdf"
    result_path = generate_audit_pdf(company, [_finding()], output_path)
    assert result_path == output_path
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    assert output_path.read_bytes()[:4] == b"%PDF"


def test_generate_audit_pdf_with_no_findings_still_produces_a_pdf(company, tmp_path):
    output_path = tmp_path / "audit.pdf"
    generate_audit_pdf(company, [], output_path)
    assert output_path.read_bytes()[:4] == b"%PDF"
