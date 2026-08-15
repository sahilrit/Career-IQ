"""Deliverable generation: turns a unified list of findings (plus an
optional ROI estimate) into every format a freelance pitch needs —
Loom script, PDF, email, LinkedIn message, proposal. All deterministic,
template-based text generation; nothing about the company or the user
is invented beyond what's in the findings and the Career Brain.
"""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from careeros_audit_proposal_engine.finding import Finding
from careeros_audit_proposal_engine.roi_estimate import ROIEstimate
from careeros_career_brain import CareerBrain
from careeros_client_acquisition import Company

_LINKEDIN_MAX_CHARS = 300


def render_loom_script(company: Company, findings: list[Finding]) -> str:
    lines = [
        f"[Intro] Hey — I put together a quick walkthrough of {company.name}'s site.",
        "",
    ]
    for finding in findings:
        lines.append(f"[{finding.category}] {finding.detail}. {finding.recommendation}")
    lines.append("")
    lines.append("[Close] Happy to walk through fixing any of this — let me know.")
    return "\n".join(lines) + "\n"


def render_audit_email(
    brain: CareerBrain, company: Company, findings: list[Finding], roi_estimate: ROIEstimate | None
) -> str:
    body_lines = [f"Hi{f' {company.contact_name}' if company.contact_name else ''},", ""]
    body_lines.append(f"I ran a quick audit on {company.name} and found a few things worth fixing:")
    body_lines.append("")
    for finding in findings[:5]:
        body_lines.append(f"- {finding.detail}")
    body_lines.append("")
    if roi_estimate is not None:
        body_lines.append(
            "Fixing these could realistically be worth roughly "
            f"${roi_estimate.projected_additional_monthly_revenue:,.0f}/month "
            f"({roi_estimate.disclaimer})"
        )
        body_lines.append("")
    body_lines.append("Happy to send over the full breakdown — worth a quick call?")
    body_lines.append("")
    body_lines.append("Best,")
    body_lines.append(brain.identity.full_name)
    return "\n".join(body_lines) + "\n"


def render_linkedin_message(company: Company, findings: list[Finding]) -> str:
    if findings:
        message = f"Hi — noticed {company.name}'s site has {findings[0].detail}. Worth a look?"
    else:
        message = f"Hi — I looked at {company.name}'s site and had a couple of ideas. Open to chat?"
    if len(message) > _LINKEDIN_MAX_CHARS:
        message = message[: _LINKEDIN_MAX_CHARS - 1].rstrip() + "…"
    return message


def render_proposal(
    brain: CareerBrain,
    company: Company,
    findings: list[Finding],
    roi_estimate: ROIEstimate | None = None,
) -> str:
    lines = [f"Proposal for {company.name}", "", "Findings:"]
    for finding in findings:
        lines.append(f"- [{finding.category}] {finding.detail} -> {finding.recommendation}")
    lines.append("")
    if roi_estimate is not None:
        lines.append(
            "Projected impact: +$"
            f"{roi_estimate.projected_additional_monthly_revenue:,.0f}/month "
            f"(+${roi_estimate.projected_additional_annual_revenue:,.0f}/year). "
            f"{roi_estimate.disclaimer}"
        )
        lines.append("")
    skill_names = [skill.name for skill in brain.skills[:3]]
    if skill_names:
        lines.append(f"Why me: my background in {', '.join(skill_names)}.")
        lines.append("")
    lines.append(f"Submitted by {brain.identity.full_name}")
    return "\n".join(lines) + "\n"


def generate_audit_pdf(company: Company, findings: list[Finding], output_path: str | Path) -> Path:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=16)
    _cell(pdf, 10, _pdf_safe(f"Audit Report - {company.name}"))
    pdf.set_font("Helvetica", size=11)
    pdf.ln(4)
    if not findings:
        _cell(pdf, 8, "No issues detected.")
    for finding in findings:
        _cell(pdf, 8, _pdf_safe(f"- {finding.detail}"))
        _cell(pdf, 8, _pdf_safe(f"  Recommendation: {finding.recommendation}"))
        pdf.ln(2)

    resolved = Path(output_path)
    pdf.output(str(resolved))
    return resolved


def _pdf_safe(text: str) -> str:
    return text.encode("latin-1", "replace").decode("latin-1")


def _cell(pdf: FPDF, height: float, text: str) -> None:
    pdf.multi_cell(0, height, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
