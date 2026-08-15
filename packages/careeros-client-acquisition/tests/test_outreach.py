"""Tests for TemplateOutreachGenerator."""

from __future__ import annotations

from careeros_client_acquisition import ProblemSignal, SignalType, TemplateOutreachGenerator
from careeros_client_acquisition.audit import generate_audit_report


def test_message_mentions_company_and_sender(brain, company):
    report = generate_audit_report(company, [])
    message = TemplateOutreachGenerator().generate(brain, company, report)
    assert company.name in message
    assert brain.identity.full_name in message


def test_message_mentions_contact_name_when_known(brain, company):
    company = company.model_copy(update={"contact_name": "Jane Smith"})
    report = generate_audit_report(company, [])
    message = TemplateOutreachGenerator().generate(brain, company, report)
    assert "Jane Smith" in message


def test_message_references_top_finding(brain, company):
    signals = [ProblemSignal(signal_type=SignalType.NO_HTTPS, detail="site served over http://")]
    report = generate_audit_report(company, signals)
    message = TemplateOutreachGenerator().generate(brain, company, report)
    assert "site served over http://" in message


def test_message_mentions_own_skills(brain, company):
    report = generate_audit_report(company, [])
    message = TemplateOutreachGenerator().generate(brain, company, report)
    assert "Shopify" in message
