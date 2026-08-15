"""Tests for the compliance readiness report."""

from __future__ import annotations

from datetime import UTC, datetime

from careeros_compliance import SecurityPolicy, generate_compliance_report

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def test_report_is_compliant_when_every_gate_passes():
    report = generate_compliance_report(
        audit_entry_count=5,
        retention_policy_count=2,
        expired_record_count=0,
        security_policy=SecurityPolicy(),
        now=_NOW,
    )
    assert report.is_compliant is True
    assert report.gates == {
        "retention_policies_configured": True,
        "security_policy_configured": True,
        "no_overdue_deletions": True,
    }


def test_report_is_not_compliant_without_retention_policies():
    report = generate_compliance_report(
        audit_entry_count=5,
        retention_policy_count=0,
        expired_record_count=0,
        security_policy=SecurityPolicy(),
        now=_NOW,
    )
    assert report.is_compliant is False
    assert report.gates["retention_policies_configured"] is False


def test_report_is_not_compliant_without_a_security_policy():
    report = generate_compliance_report(
        audit_entry_count=5,
        retention_policy_count=2,
        expired_record_count=0,
        security_policy=None,
        now=_NOW,
    )
    assert report.is_compliant is False
    assert report.security_policy_configured is False


def test_report_is_not_compliant_with_overdue_deletions():
    report = generate_compliance_report(
        audit_entry_count=5,
        retention_policy_count=2,
        expired_record_count=3,
        security_policy=SecurityPolicy(),
        now=_NOW,
    )
    assert report.is_compliant is False
    assert report.gates["no_overdue_deletions"] is False


def test_report_carries_generated_at_and_counts_through():
    report = generate_compliance_report(
        audit_entry_count=42,
        retention_policy_count=1,
        expired_record_count=0,
        security_policy=SecurityPolicy(),
        now=_NOW,
    )
    assert report.generated_at == _NOW
    assert report.audit_entry_count == 42
