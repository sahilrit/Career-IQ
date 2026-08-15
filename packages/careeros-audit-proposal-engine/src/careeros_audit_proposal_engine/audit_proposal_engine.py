"""AuditProposalEngine: the facade that merges baseline website signals
(Phase 31) with the deep Shopify/Meta Ads audits from this package into
one findings list, then generates every deliverable a freelance pitch
needs from it.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from careeros_audit_proposal_engine.finding import Finding
from careeros_audit_proposal_engine.meta_ads_audit import MetaAdsAuditProvider, audit_meta_ads
from careeros_audit_proposal_engine.outputs import (
    generate_audit_pdf,
    render_audit_email,
    render_linkedin_message,
    render_loom_script,
    render_proposal,
)
from careeros_audit_proposal_engine.roi_estimate import ROIEstimate, ROIInputs, estimate_roi
from careeros_audit_proposal_engine.shopify_audit import ShopifyAuditor
from careeros_career_brain import CareerBrain
from careeros_client_acquisition import AuditFinding as BaselineAuditFinding
from careeros_client_acquisition import Company


def from_baseline_finding(finding: BaselineAuditFinding) -> Finding:
    return Finding(
        category=finding.signal_type.value,
        detail=finding.detail,
        recommendation=finding.recommendation,
    )


class AuditDeliverables(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    findings: list[Finding]
    roi_estimate: ROIEstimate | None
    loom_script: str
    email: str
    linkedin_message: str
    proposal: str
    pdf_path: Path


class AuditProposalEngine:
    def __init__(
        self,
        *,
        shopify_auditor: ShopifyAuditor | None = None,
        meta_ads_provider: MetaAdsAuditProvider | None = None,
    ) -> None:
        self._shopify_auditor = shopify_auditor
        self._meta_ads_provider = meta_ads_provider

    def collect_findings(
        self, company: Company, baseline_findings: list[BaselineAuditFinding] | None = None
    ) -> list[Finding]:
        findings = [from_baseline_finding(f) for f in (baseline_findings or [])]
        if self._shopify_auditor is not None:
            findings.extend(self._shopify_auditor.audit(company))
        if self._meta_ads_provider is not None:
            ads = self._meta_ads_provider.collect(company)
            findings.extend(audit_meta_ads(ads))
        return findings

    def generate_deliverables(
        self,
        brain: CareerBrain,
        company: Company,
        findings: list[Finding],
        *,
        roi_inputs: ROIInputs | None = None,
        pdf_output_path: str | Path,
    ) -> AuditDeliverables:
        roi_estimate: ROIEstimate | None = None
        if roi_inputs is not None:
            roi_estimate = estimate_roi(roi_inputs, len(findings))

        pdf_path = generate_audit_pdf(company, findings, pdf_output_path)

        return AuditDeliverables(
            findings=findings,
            roi_estimate=roi_estimate,
            loom_script=render_loom_script(company, findings),
            email=render_audit_email(brain, company, findings, roi_estimate),
            linkedin_message=render_linkedin_message(company, findings),
            proposal=render_proposal(brain, company, findings, roi_estimate),
            pdf_path=pdf_path,
        )
