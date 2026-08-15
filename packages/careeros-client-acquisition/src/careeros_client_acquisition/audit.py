"""Lightweight audit report generation: turns detected problem signals
into plain-language findings and recommendations. Phase 32 (AI Audit &
Proposal Engine) builds the deep, source-specific audits (Shopify
UX/CRO/checkout, Meta Ads) — this is the general-purpose baseline every
prospect gets regardless of which discovery source found them.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from careeros_client_acquisition.company import Company
from careeros_client_acquisition.signals import ProblemSignal, SignalType

_RECOMMENDATIONS: dict[SignalType, str] = {
    SignalType.NO_HTTPS: (
        "Move the site to HTTPS — visitors and search engines both penalize plain HTTP."
    ),
    SignalType.MISSING_META_DESCRIPTION: (
        "Add a meta description — it's free organic click-through rate left on the table."
    ),
    SignalType.NO_TESTIMONIALS: (
        "Add a testimonials or reviews section — social proof measurably lifts conversion."
    ),
    SignalType.NO_LIVE_CHAT: (
        "Add a live chat widget — it captures visitors who'd otherwise bounce unanswered."
    ),
    SignalType.THIN_HOMEPAGE_CONTENT: (
        "Expand the homepage content — thin pages under-perform in both SEO and trust."
    ),
}


class AuditFinding(BaseModel):
    signal_type: SignalType
    detail: str
    recommendation: str


class AuditReport(BaseModel):
    company_id: str
    findings: list[AuditFinding]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def generate_audit_report(company: Company, signals: list[ProblemSignal]) -> AuditReport:
    findings = [
        AuditFinding(
            signal_type=signal.signal_type,
            detail=signal.detail,
            recommendation=_RECOMMENDATIONS[signal.signal_type],
        )
        for signal in signals
    ]
    return AuditReport(company_id=company.id, findings=findings)


def render_audit_report(company: Company, report: AuditReport) -> str:
    lines = [f"Website Audit — {company.name}", ""]
    if not report.findings:
        lines.append("No issues detected.")
    for finding in report.findings:
        lines.append(f"- {finding.detail}")
        lines.append(f"  -> {finding.recommendation}")
    return "\n".join(lines) + "\n"
