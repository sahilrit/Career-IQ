"""Audit & Proposal — the freelance money-maker. Generate a full pitch kit
(findings, ROI, cold email, LinkedIn DM, Loom script, written proposal, and
a PDF) for a target business. AI-writes the proposal when a key is set.

Runs without a browser (no live storefront crawl on the free tier): findings
come from the manually-entered Meta ads audit, so it works anywhere."""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from careeros_ai import AIError
from careeros_api import ai_support
from careeros_api.dependencies import Context
from careeros_api.storefront_audit import audit_storefront
from careeros_audit_proposal_engine import (
    AdCreative,
    AuditProposalEngine,
    ManualMetaAdsAuditProvider,
    ROIInputs,
)
from careeros_career_brain import CareerBrainRepository
from careeros_client_acquisition import Company

router = APIRouter(prefix="/audit", tags=["audit"])

_SYSTEM = (
    "You are a senior freelance consultant writing a short, persuasive project "
    "proposal to a prospective client. Use ONLY the facts provided (the consultant's "
    "background, the client, the audit findings, the ROI estimate). Never invent "
    "metrics, employers, or credentials. Be concrete and specific. 200-320 words."
)


class AdInput(BaseModel):
    headline: str = ""
    body_text: str = ""
    cta: str = ""
    landing_page_url: str = ""


class PitchKitRequest(BaseModel):
    company_name: str = Field(min_length=1)
    website: str = ""
    industry: str = ""
    monthly_visitors: int | None = None
    conversion_rate: float | None = None
    average_order_value: float | None = None
    ads: list[AdInput] = Field(default_factory=list)


def _brain(context: Context):
    brains = CareerBrainRepository(context.store).list_all()
    if not brains:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "create a Career Brain first")
    return brains[0]


def _ai_proposal(client, brain, company, findings, roi_estimate) -> str:
    identity = brain.identity
    skills = ", ".join(skill.name for skill in brain.skills) or "(none listed)"
    findings_text = (
        "\n".join(f"- [{f.category}] {f.detail} → {f.recommendation}" for f in findings)
        or "(no specific findings)"
    )
    if roi_estimate is not None:
        annual = roi_estimate.projected_additional_annual_revenue
        roi_text = f"Estimated additional revenue: ~${annual:,.0f}/yr"
    else:
        roi_text = "(no ROI estimate provided)"
    prompt = (
        f"Consultant: {identity.full_name}\n"
        f"Headline: {identity.headline}\n"
        f"Summary: {identity.summary}\n"
        f"Skills: {skills}\n\n"
        f"Client: {company.name} ({company.industry or 'industry n/a'}) — {company.website}\n"
        f"Audit findings:\n{findings_text}\n\n"
        f"{roi_text}\n\n"
        f"Write the proposal, signed '{identity.full_name}'."
    )
    return client.complete(system=_SYSTEM, prompt=prompt)


@router.post("/pitch-kit")
def pitch_kit(body: PitchKitRequest, context: Context) -> dict[str, Any]:
    brain = _brain(context)
    company = Company(name=body.company_name, website=body.website, industry=body.industry)

    ads = [
        AdCreative(
            headline=ad.headline,
            body_text=ad.body_text,
            cta=ad.cta,
            landing_page_url=ad.landing_page_url,
            destination_is_dedicated_landing_page=bool(ad.landing_page_url),
        )
        for ad in body.ads
    ]
    provider = ManualMetaAdsAuditProvider(ads) if ads else None
    engine = AuditProposalEngine(meta_ads_provider=provider)
    findings = engine.collect_findings(company)

    # Audit the real storefront over HTTP (no browser) when a site is given.
    if body.website:
        findings = audit_storefront(body.website) + findings

    roi_inputs = None
    if (
        body.monthly_visitors is not None
        and body.conversion_rate is not None
        and body.average_order_value is not None
    ):
        roi_inputs = ROIInputs(
            monthly_visitors=body.monthly_visitors,
            conversion_rate=body.conversion_rate,
            average_order_value=body.average_order_value,
        )

    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = Path(tmp) / "proposal.pdf"
        deliverables = engine.generate_deliverables(
            brain, company, findings, roi_inputs=roi_inputs, pdf_output_path=pdf_path
        )
        pdf_base64 = base64.b64encode(deliverables.pdf_path.read_bytes()).decode("ascii")

    proposal = deliverables.proposal
    ai_used = False
    client = ai_support.resolve_ai_client(context.store, context.account.workspace_id)
    if client is not None:
        try:
            proposal = _ai_proposal(client, brain, company, findings, deliverables.roi_estimate)
            ai_used = True
        except AIError:
            proposal = deliverables.proposal  # fall back to template
            ai_used = False

    roi = None
    if deliverables.roi_estimate is not None:
        estimate = deliverables.roi_estimate
        roi = {
            "current_monthly_revenue": estimate.current_monthly_revenue,
            "assumed_uplift_pct": estimate.assumed_uplift_pct,
            "projected_additional_monthly_revenue": estimate.projected_additional_monthly_revenue,
            "projected_additional_annual_revenue": estimate.projected_additional_annual_revenue,
            "disclaimer": estimate.disclaimer,
        }

    return {
        "findings": [
            {"category": f.category, "detail": f.detail, "recommendation": f.recommendation}
            for f in findings
        ],
        "roi": roi,
        "email": deliverables.email,
        "linkedin_message": deliverables.linkedin_message,
        "loom_script": deliverables.loom_script,
        "proposal": proposal,
        "ai_used": ai_used,
        "pdf_base64": pdf_base64,
    }
