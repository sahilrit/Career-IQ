"""Freelance client-acquisition glue for the dashboard, kept
Streamlit-free so it's testable.

Wires the already-shipped client-acquisition pipeline (Company ->
website audit -> opportunity score -> qualify -> outreach draft ->
pipeline stages) into click-only actions. The website audit visits a
prospect's OWN public site and reports fixable problems — the same
thing a marketing consultant does by hand. Outreach is DRAFTED for the
user to send; nothing is messaged automatically.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from careeros_audit_proposal_engine import (
    AuditDeliverables,
    AuditProposalEngine,
    ROIInputs,
    ShopifyAuditor,
)
from careeros_browser import BrowserSession, launch_browser_session
from careeros_career_brain import CareerBrain
from careeros_client_acquisition import (
    AuditReport,
    ClientAcquisitionProgressRepository,
    ClientAcquisitionStage,
    Company,
    CompanyRepository,
    IdealClientProfile,
    ProblemSignal,
    TemplateOutreachGenerator,
    WebsiteSignalDetector,
    generate_audit_report,
    qualify,
    render_audit_report,
    score_company_opportunity,
)
from careeros_common import DocumentStore
from careeros_financial_intelligence import IncomeRecord, IncomeRepository, IncomeSource
from careeros_opportunity_intelligence import Client, ClientRepository, RelationshipStage


@dataclass
class AuditOutcome:
    company: Company
    signals: list[ProblemSignal]
    report: AuditReport
    report_text: str
    opportunity_score: float
    qualified: bool
    outreach_message: str


def add_company(store: DocumentStore, *, name: str, website: str, industry: str = "") -> Company:
    website = website.strip()
    if website and not website.startswith(("http://", "https://")):
        website = f"https://{website}"
    company = Company(name=name.strip(), website=website, industry=industry.strip())
    CompanyRepository(store).save(company)
    ClientAcquisitionProgressRepository(store).mark_complete(
        company.id, ClientAcquisitionStage.DISCOVERY
    )
    return company


def list_companies(store: DocumentStore) -> list[Company]:
    return CompanyRepository(store).list_all()


def audit_company(
    store: DocumentStore,
    brain: CareerBrain,
    company: Company,
    *,
    profile: IdealClientProfile | None = None,
    session: BrowserSession | None = None,
) -> AuditOutcome:
    """Visit the company's public website, detect fixable problems, score
    the opportunity, and draft outreach. Records the pipeline stages."""

    def run(active_session: BrowserSession) -> AuditOutcome:
        signals = WebsiteSignalDetector(active_session).detect(company)
        report = generate_audit_report(company, signals)
        score = score_company_opportunity(signals)
        is_qualified = qualify(company, signals, profile or IdealClientProfile())
        outreach = TemplateOutreachGenerator().generate(brain, company, report)

        progress = ClientAcquisitionProgressRepository(store)
        for stage in (
            ClientAcquisitionStage.QUALIFICATION,
            ClientAcquisitionStage.PROBLEM_DETECTION,
            ClientAcquisitionStage.OPPORTUNITY_SCORE,
            ClientAcquisitionStage.AUDIT,
        ):
            progress.mark_complete(company.id, stage)

        return AuditOutcome(
            company=company,
            signals=signals,
            report=report,
            report_text=render_audit_report(company, report),
            opportunity_score=score,
            qualified=is_qualified,
            outreach_message=outreach,
        )

    if session is not None:
        return run(session)
    with launch_browser_session(headless=True) as active_session:
        return run(active_session)


def generate_deep_deliverables(
    store: DocumentStore,
    brain: CareerBrain,
    company: Company,
    *,
    monthly_visitors: int,
    conversion_rate: float,
    average_order_value: float,
    output_dir: str | Path = ".careeros/proposals",
    session: BrowserSession | None = None,
) -> AuditDeliverables:
    """Run the deep Shopify storefront audit, estimate ROI from the
    prospect's traffic/economics, and generate every pitch deliverable
    (Loom script, email, LinkedIn message, written proposal, and a PDF).

    ROI is a transparent projection with a disclaimer, not a promise.
    Records the PROPOSAL stage.
    """
    output_path = Path(output_dir) / f"proposal-{company.id}.pdf"

    def run(active_session: BrowserSession) -> AuditDeliverables:
        engine = AuditProposalEngine(shopify_auditor=ShopifyAuditor(active_session))
        # Fold the free website signals in as baseline findings so the deep
        # audit builds on them. collect_findings expects AuditFindings (which
        # carry a recommendation), so convert the raw signals via the report.
        signals = WebsiteSignalDetector(active_session).detect(company)
        baseline = generate_audit_report(company, signals).findings
        findings = engine.collect_findings(company, baseline)
        deliverables = engine.generate_deliverables(
            brain,
            company,
            findings,
            roi_inputs=ROIInputs(
                monthly_visitors=monthly_visitors,
                conversion_rate=conversion_rate,
                average_order_value=average_order_value,
            ),
            pdf_output_path=output_path,
        )
        ClientAcquisitionProgressRepository(store).mark_complete(
            company.id, ClientAcquisitionStage.PROPOSAL
        )
        return deliverables

    if session is not None:
        return run(session)
    with launch_browser_session(headless=True) as active_session:
        return run(active_session)


def mark_outreach_sent(store: DocumentStore, company: Company) -> None:
    ClientAcquisitionProgressRepository(store).mark_complete(
        company.id, ClientAcquisitionStage.OUTREACH
    )


def promote_to_client(
    store: DocumentStore,
    company: Company,
    *,
    stage: RelationshipStage = RelationshipStage.CONTACTED,
) -> Client:
    clients = ClientRepository(store)
    existing = clients.find_by_name(company.name)
    client = existing or Client(name=company.name, contact_email=company.contact_email)
    client.stage = stage
    clients.save(client)
    return client


def record_client_income(
    store: DocumentStore, *, client_name: str, amount: float, received_date, hours_worked=None
) -> IncomeRecord:
    record = IncomeRecord(
        source=IncomeSource.FREELANCE,
        source_name=client_name,
        amount=amount,
        received_date=received_date,
        hours_worked=hours_worked,
    )
    IncomeRepository(store).save(record)
    return record
