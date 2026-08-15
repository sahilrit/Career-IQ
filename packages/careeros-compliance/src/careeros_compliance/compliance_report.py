"""Compliance readiness report: a pure aggregator over caller-supplied
counts, the same combinator philosophy as Phase 40's Career
Intelligence and Phase 41's CEO Agent — this module doesn't recompute
retention or audit state itself, it just reports on it.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from careeros_compliance.security_policy import SecurityPolicy


class ComplianceReport(BaseModel):
    generated_at: datetime
    audit_entry_count: int
    retention_policy_count: int
    expired_record_count: int
    security_policy_configured: bool
    gates: dict[str, bool]

    @property
    def is_compliant(self) -> bool:
        return all(self.gates.values())


def generate_compliance_report(
    *,
    audit_entry_count: int,
    retention_policy_count: int,
    expired_record_count: int,
    security_policy: SecurityPolicy | None,
    now: datetime,
) -> ComplianceReport:
    gates = {
        "retention_policies_configured": retention_policy_count > 0,
        "security_policy_configured": security_policy is not None,
        "no_overdue_deletions": expired_record_count == 0,
    }
    return ComplianceReport(
        generated_at=now,
        audit_entry_count=audit_entry_count,
        retention_policy_count=retention_policy_count,
        expired_record_count=expired_record_count,
        security_policy_configured=security_policy is not None,
        gates=gates,
    )
