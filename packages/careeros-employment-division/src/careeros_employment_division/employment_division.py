"""EmploymentDivision completes the employment agency by (a) filling the
remaining pipeline gaps — portfolio summaries, recruiter outreach,
follow-ups — with real generators sourced from Career Brain, and (b)
tracking pipeline progress via events already published by every
earlier phase, so nothing here needs a direct dependency on job
discovery, application execution, or interview intelligence.

    Discovery -> Scoring -> Research -> Resume -> Portfolio -> Cover Letter
    -> Recruiter Outreach -> Application -> Follow-up -> Interview -> Offer
    -> Negotiation

Additional job/freelance sources plug in through the existing provider
registries (Phase 6/18/24) this pipeline already runs on top of —
nothing in the pipeline is hardcoded to a specific provider.
"""

from __future__ import annotations

from careeros_career_brain import Application, CareerBrain, Recruiter
from careeros_employment_division.events import wire_pipeline_progress
from careeros_employment_division.follow_up import generate_follow_up_message
from careeros_employment_division.pipeline_stage import (
    PipelineProgress,
    PipelineProgressRepository,
    PipelineStage,
)
from careeros_employment_division.portfolio import PortfolioSummary, build_portfolio_summary
from careeros_employment_division.recruiter_outreach import (
    RecruiterOutreachGenerator,
    TemplateRecruiterOutreachGenerator,
)
from careeros_event_bus import EventBus
from careeros_job_providers import JobPosting


class EmploymentDivision:
    def __init__(
        self,
        progress_repository: PipelineProgressRepository,
        *,
        recruiter_outreach_generator: RecruiterOutreachGenerator | None = None,
    ) -> None:
        self._progress_repository = progress_repository
        self._recruiter_outreach_generator = (
            recruiter_outreach_generator or TemplateRecruiterOutreachGenerator()
        )

    @staticmethod
    def wire_events(bus: EventBus, progress_repository: PipelineProgressRepository) -> None:
        wire_pipeline_progress(bus, progress_repository)

    def build_portfolio(self, brain: CareerBrain) -> PortfolioSummary:
        return build_portfolio_summary(brain)

    def draft_recruiter_outreach(
        self, brain: CareerBrain, recruiter: Recruiter, posting: JobPosting
    ) -> str:
        return self._recruiter_outreach_generator.generate(brain, recruiter, posting)

    def draft_follow_up(self, application: Application, *, days_since_applied: int) -> str:
        return generate_follow_up_message(application, days_since_applied=days_since_applied)

    def progress_for(self, application_id: str) -> PipelineProgress:
        return self._progress_repository.load(application_id)

    def mark_research_done(self, application_id: str) -> PipelineProgress:
        return self._progress_repository.mark_complete(application_id, PipelineStage.RESEARCH)

    def mark_resume_done(self, application_id: str) -> PipelineProgress:
        return self._progress_repository.mark_complete(application_id, PipelineStage.RESUME)

    def mark_portfolio_done(self, application_id: str) -> PipelineProgress:
        return self._progress_repository.mark_complete(application_id, PipelineStage.PORTFOLIO)

    def mark_cover_letter_done(self, application_id: str) -> PipelineProgress:
        return self._progress_repository.mark_complete(application_id, PipelineStage.COVER_LETTER)

    def mark_recruiter_outreach_done(self, application_id: str) -> PipelineProgress:
        return self._progress_repository.mark_complete(
            application_id, PipelineStage.RECRUITER_OUTREACH
        )

    def mark_follow_up_done(self, application_id: str) -> PipelineProgress:
        return self._progress_repository.mark_complete(application_id, PipelineStage.FOLLOW_UP)
