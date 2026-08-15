"""Tests for generate_audit_report / render_audit_report."""

from __future__ import annotations

from careeros_client_acquisition import ProblemSignal, SignalType
from careeros_client_acquisition.audit import generate_audit_report, render_audit_report


def test_no_signals_produces_no_findings(company):
    report = generate_audit_report(company, [])
    assert report.findings == []


def test_each_signal_becomes_a_finding_with_a_recommendation(company):
    signals = [ProblemSignal(signal_type=SignalType.NO_HTTPS, detail="http://x")]
    report = generate_audit_report(company, signals)
    assert len(report.findings) == 1
    assert report.findings[0].signal_type == SignalType.NO_HTTPS
    assert "HTTPS" in report.findings[0].recommendation


def test_render_includes_company_name_and_findings(company):
    signals = [ProblemSignal(signal_type=SignalType.NO_HTTPS, detail="http://x")]
    report = generate_audit_report(company, signals)
    rendered = render_audit_report(company, report)
    assert company.name in rendered
    assert "http://x" in rendered


def test_render_with_no_findings_says_so(company):
    report = generate_audit_report(company, [])
    rendered = render_audit_report(company, report)
    assert "No issues detected" in rendered
