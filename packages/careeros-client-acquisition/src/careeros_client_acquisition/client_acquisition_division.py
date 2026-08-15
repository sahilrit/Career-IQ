"""ClientAcquisitionDivision: the facade tying discovery, signal
detection, qualification, scoring, audit, outreach, and follow-up
together, and tracking a company's progress through the pipeline.

Proposal/Call/Contract are tracked here as pipeline stages, but their
content generation is intentionally out of scope for this package —
Phase 32 (AI Audit & Proposal Engine) supplies deeper, source-specific
audit and proposal generators that plug into the AUDIT/PROPOSAL stages,
the same way Phase 12's application-engine supplies the resume content
that Phase 30's Employment Division only tracks progress for.

Winning a company (``win_client``) hands it off to
careeros_opportunity_intelligence's Client CRM (Phase 20) — that
package, not this one, owns what happens to a relationship after the
contract is signed.
"""

from __future__ import annotations

from careeros_career_brain import CareerBrain
from careeros_client_acquisition.audit import AuditReport, generate_audit_report
from careeros_client_acquisition.company import Company, CompanyRepository
from careeros_client_acquisition.discovery import CompanyDiscoveryProvider, CompanyDiscoveryQuery
from careeros_client_acquisition.follow_up import generate_follow_up_message
from careeros_client_acquisition.outreach import OutreachGenerator, TemplateOutreachGenerator
from careeros_client_acquisition.pipeline_stage import (
    ClientAcquisitionProgress,
    ClientAcquisitionProgressRepository,
    ClientAcquisitionStage,
)
from careeros_client_acquisition.qualification import IdealClientProfile, qualify
from careeros_client_acquisition.scoring import score_company_opportunity
from careeros_client_acquisition.signals import ProblemSignal, WebsiteSignalDetector
from careeros_event_bus import Event, EventBus
from careeros_opportunity_intelligence import Client, ClientRepository, RelationshipStage


class ClientAcquisitionDivision:
    def __init__(
        self,
        company_repository: CompanyRepository,
        progress_repository: ClientAcquisitionProgressRepository,
        client_repository: ClientRepository,
        *,
        discovery_provider: CompanyDiscoveryProvider,
        outreach_generator: OutreachGenerator | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._companies = company_repository
        self._progress = progress_repository
        self._clients = client_repository
        self._discovery_provider = discovery_provider
        self._outreach_generator = outreach_generator or TemplateOutreachGenerator()
        self._bus = event_bus

    def _publish(self, event_type: str, company_id: str, **extra: object) -> None:
        if self._bus is None:
            return
        self._bus.publish(Event(event_type=event_type, payload={"subject_id": company_id, **extra}))

    def discover(self, query: CompanyDiscoveryQuery) -> list[Company]:
        companies = self._discovery_provider.discover(query)
        for company in companies:
            self._companies.save(company)
            self._progress.mark_complete(company.id, ClientAcquisitionStage.DISCOVERY)
            self._publish("company.discovered", company.id)
        return companies

    def qualify_company(
        self, company: Company, signals: list[ProblemSignal], profile: IdealClientProfile
    ) -> bool:
        is_qualified = qualify(company, signals, profile)
        if is_qualified:
            self._progress.mark_complete(company.id, ClientAcquisitionStage.QUALIFICATION)
            self._publish("company.qualified", company.id)
        return is_qualified

    def detect_problems(
        self, company: Company, detector: WebsiteSignalDetector
    ) -> list[ProblemSignal]:
        signals = detector.detect(company)
        self._progress.mark_complete(company.id, ClientAcquisitionStage.PROBLEM_DETECTION)
        return signals

    def score(self, company: Company, signals: list[ProblemSignal]) -> float:
        self._progress.mark_complete(company.id, ClientAcquisitionStage.OPPORTUNITY_SCORE)
        return score_company_opportunity(signals)

    def generate_audit(self, company: Company, signals: list[ProblemSignal]) -> AuditReport:
        report = generate_audit_report(company, signals)
        self._progress.mark_complete(company.id, ClientAcquisitionStage.AUDIT)
        self._publish("company.audit_generated", company.id)
        return report

    def draft_outreach(self, brain: CareerBrain, company: Company, report: AuditReport) -> str:
        message = self._outreach_generator.generate(brain, company, report)
        self._progress.mark_complete(company.id, ClientAcquisitionStage.OUTREACH)
        return message

    def draft_follow_up(self, company: Company, *, days_since_outreach: int) -> str:
        message = generate_follow_up_message(company, days_since_outreach=days_since_outreach)
        self._progress.mark_complete(company.id, ClientAcquisitionStage.FOLLOW_UP)
        return message

    def mark_proposal_sent(self, company: Company) -> ClientAcquisitionProgress:
        return self._progress.mark_complete(company.id, ClientAcquisitionStage.PROPOSAL)

    def mark_call_scheduled(self, company: Company) -> ClientAcquisitionProgress:
        return self._progress.mark_complete(company.id, ClientAcquisitionStage.CALL)

    def mark_contract_signed(self, company: Company) -> ClientAcquisitionProgress:
        return self._progress.mark_complete(company.id, ClientAcquisitionStage.CONTRACT)

    def win_client(self, company: Company) -> Client:
        client = Client(
            name=company.name,
            contact_email=company.contact_email,
            stage=RelationshipStage.ACTIVE,
        )
        self._clients.save(client)
        self._progress.mark_complete(company.id, ClientAcquisitionStage.CLIENT)
        self._publish("client.won", company.id, client_id=client.id)
        return client

    def progress_for(self, company_id: str) -> ClientAcquisitionProgress:
        return self._progress.load(company_id)
