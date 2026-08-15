"""careeros_client_acquisition: the Freelance Client Acquisition Division.

Company Discovery -> Qualification -> Problem Detection ->
Opportunity Score -> Audit -> Outreach -> Follow-up -> Proposal ->
Call -> Contract -> Client.
"""

from careeros_client_acquisition.audit import (
    AuditFinding,
    AuditReport,
    generate_audit_report,
    render_audit_report,
)
from careeros_client_acquisition.client_acquisition_division import ClientAcquisitionDivision
from careeros_client_acquisition.company import Company, CompanyRepository
from careeros_client_acquisition.discovery import (
    CompanyDiscoveryProvider,
    CompanyDiscoveryQuery,
    ManualCompanyDiscoveryProvider,
)
from careeros_client_acquisition.exceptions import ClientAcquisitionError
from careeros_client_acquisition.follow_up import generate_follow_up_message
from careeros_client_acquisition.outreach import OutreachGenerator, TemplateOutreachGenerator
from careeros_client_acquisition.pipeline_stage import (
    ClientAcquisitionProgress,
    ClientAcquisitionProgressRepository,
    ClientAcquisitionStage,
)
from careeros_client_acquisition.qualification import IdealClientProfile, qualify
from careeros_client_acquisition.scoring import score_company_opportunity
from careeros_client_acquisition.signals import (
    ProblemSignal,
    SignalType,
    WebsiteSignalDetector,
    WebsiteSignalRules,
)

__all__ = [
    "AuditFinding",
    "AuditReport",
    "ClientAcquisitionDivision",
    "ClientAcquisitionError",
    "ClientAcquisitionProgress",
    "ClientAcquisitionProgressRepository",
    "ClientAcquisitionStage",
    "Company",
    "CompanyDiscoveryProvider",
    "CompanyDiscoveryQuery",
    "CompanyRepository",
    "IdealClientProfile",
    "ManualCompanyDiscoveryProvider",
    "OutreachGenerator",
    "ProblemSignal",
    "SignalType",
    "TemplateOutreachGenerator",
    "WebsiteSignalDetector",
    "WebsiteSignalRules",
    "generate_audit_report",
    "generate_follow_up_message",
    "qualify",
    "render_audit_report",
    "score_company_opportunity",
]
