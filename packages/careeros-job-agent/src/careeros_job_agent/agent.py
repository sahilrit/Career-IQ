"""JobAgent: the autonomous opportunity-discovery loop.

Career Brain -> Job Discovery -> Matching -> Scoring -> Prioritization ->
Action. The "action" at this phase is qualification: moving a newly
discovered, high-scoring application from DISCOVERED to QUALIFIED and
publishing an event about it. Actually applying (Phase 12's Application
Engine, Phase 21-22's autonomous execution) comes later — this agent only
ever updates Career Brain's own bookkeeping, never touches an external
site or fabricates anything about the opportunity.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from careeros_career_brain import ApplicationStatus, CareerBrainRepository
from careeros_event_bus import Event, EventBus
from careeros_job_agent.policy import QualificationPolicy
from careeros_job_discovery import JobDiscoveryPipeline
from careeros_job_providers import JobSearchQuery


class CycleSummary(BaseModel):
    """The outcome of one discovery cycle, including why sources went quiet."""

    discovered: int = 0
    qualified: int = 0
    source_errors: list[str] = Field(default_factory=list)


class JobAgent:
    def __init__(
        self,
        pipeline: JobDiscoveryPipeline,
        repository: CareerBrainRepository,
        event_bus: EventBus,
        *,
        policy: QualificationPolicy | None = None,
    ) -> None:
        self._pipeline = pipeline
        self._repository = repository
        self._bus = event_bus
        self._policy = policy or QualificationPolicy()

    def run_cycle(self, identity_id: str, query: JobSearchQuery) -> CycleSummary:
        """Discover new opportunities, then qualify the ones worth pursuing.

        Returns a summary of how many were discovered and qualified this cycle.
        """
        run = self._pipeline.run(identity_id, query)
        new_applications = run.applications
        if not new_applications:
            return CycleSummary(source_errors=run.source_errors)

        brain = self._repository.load(identity_id)
        qualified_count = 0
        for application in new_applications:
            brain_application = brain.find_application(application.id)
            if brain_application is None:
                continue
            if not self._policy.is_qualified(brain_application.match_score):
                continue

            brain_application.transition_to(
                ApplicationStatus.QUALIFIED, note="passed automated qualification"
            )
            qualified_count += 1
            self._bus.publish(
                Event(
                    event_type="application.status_changed",
                    source="job-agent",
                    payload={
                        "subject_id": brain_application.id,
                        "new_status": ApplicationStatus.QUALIFIED.value,
                        "match_score": brain_application.match_score,
                    },
                )
            )

        if qualified_count:
            self._repository.save(brain)

        return CycleSummary(
            discovered=len(new_applications),
            qualified=qualified_count,
            source_errors=run.source_errors,
        )
