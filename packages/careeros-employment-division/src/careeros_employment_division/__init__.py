"""careeros_employment_division: completes the employment agency pipeline
— Discovery -> Scoring -> Research -> Resume -> Portfolio -> Cover
Letter -> Recruiter Outreach -> Application -> Follow-up -> Interview ->
Offer -> Negotiation — composing every earlier phase via events rather
than tight coupling.
"""

from careeros_employment_division.employment_division import EmploymentDivision
from careeros_employment_division.events import handle_event, wire_pipeline_progress
from careeros_employment_division.follow_up import generate_follow_up_message
from careeros_employment_division.pipeline_stage import (
    PipelineProgress,
    PipelineProgressRepository,
    PipelineStage,
)
from careeros_employment_division.portfolio import (
    PortfolioCertification,
    PortfolioEducation,
    PortfolioProject,
    PortfolioSummary,
    build_portfolio_summary,
    render_portfolio_summary,
)
from careeros_employment_division.recruiter_outreach import (
    RecruiterOutreachGenerator,
    TemplateRecruiterOutreachGenerator,
)

__all__ = [
    "EmploymentDivision",
    "PipelineProgress",
    "PipelineProgressRepository",
    "PipelineStage",
    "PortfolioCertification",
    "PortfolioEducation",
    "PortfolioProject",
    "PortfolioSummary",
    "RecruiterOutreachGenerator",
    "TemplateRecruiterOutreachGenerator",
    "build_portfolio_summary",
    "generate_follow_up_message",
    "handle_event",
    "render_portfolio_summary",
    "wire_pipeline_progress",
]
