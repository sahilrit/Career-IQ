"""The end-to-end job discovery pipeline: discover -> normalize -> dedupe
-> score -> store -> emit.

Provider normalization and cross-provider dedup already happen inside
``JobProviderRegistry.search_all``. This module is the glue: it turns
surviving postings into ``Application`` records on a specific user's
Career Brain, scored against their profile, and publishes events so any
other package (Memory, a future autonomous agent, ...) can react without
this pipeline knowing who's listening.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from careeros_career_brain import Application, CareerBrainRepository
from careeros_event_bus import Event, EventBus
from careeros_job_discovery.llm_scoring import LlmJobScorer, apply_patches
from careeros_job_discovery.posting_store import JobPostingRepository
from careeros_job_discovery.scoring import score_posting
from careeros_job_providers import JobProviderRegistry, JobSearchQuery


def _profile_summary(brain) -> str:
    """A compact plain-text profile for the scoring prompt.

    Deliberately small: the whole Career Brain would dominate the context
    window, and the model only needs enough to judge fit.
    """
    preferences = brain.preferences
    lines = [
        f"Name: {brain.identity.full_name}",
        f"Skills: {', '.join(skill.name for skill in brain.skills) or 'not stated'}",
    ]
    if preferences.desired_titles:
        lines.append(f"Target roles: {', '.join(preferences.desired_titles)}")
    if preferences.desired_locations:
        lines.append(f"Preferred locations: {', '.join(preferences.desired_locations)}")
    if preferences.min_salary is not None:
        lines.append(f"Minimum salary: {preferences.min_salary}")
    if preferences.remote_only:
        lines.append("Remote only: yes")
    for experience in brain.experiences[:5]:
        lines.append(f"Experience: {experience.title} at {experience.company_name}")
    return "\n".join(lines)


class DiscoveryRun(BaseModel):
    """What one discovery cycle produced.

    ``source_errors`` carries the reason any provider contributed nothing —
    rate limited, timed out, blocked. A run that quietly returns fewer results
    because a source broke is indistinguishable from a slow week in the market,
    so these travel with the applications rather than only reaching the log.
    """

    applications: list[Application] = Field(default_factory=list)
    source_errors: list[str] = Field(default_factory=list)


class JobDiscoveryPipeline:
    def __init__(
        self,
        provider_registry: JobProviderRegistry,
        career_brain_repository: CareerBrainRepository,
        event_bus: EventBus,
        posting_repository: JobPostingRepository | None = None,
        *,
        llm_scorer: LlmJobScorer | None = None,
    ) -> None:
        self._providers = provider_registry
        self._repository = career_brain_repository
        self._bus = event_bus
        self._postings = posting_repository
        # Optional second-pass scorer. Without one, discovery behaves exactly
        # as it always has: cheap arithmetic against the Career Brain.
        self._llm_scorer = llm_scorer

    def run(self, identity_id: str, query: JobSearchQuery) -> DiscoveryRun:
        """Discover, score, and store new applications for one user's Career Brain.

        Postings already recorded (matched by job URL) are skipped, so
        running this repeatedly only ever adds genuinely new opportunities.
        """
        brain = self._repository.load(identity_id)
        result = self._providers.search_all(query)

        profile_summary = _profile_summary(brain)
        new_applications: list[Application] = []
        for posting in result.postings:
            if brain.find_application_by_job_url(posting.url) is not None:
                # Already recorded; still nothing to re-cache or re-score.
                continue

            self._bus.publish(
                Event(
                    event_type="job.discovered",
                    source=posting.source_provider,
                    payload={"job_url": posting.url, "title": posting.title},
                )
            )

            score = score_posting(posting, brain)

            if self._llm_scorer is not None:
                llm_result = self._llm_scorer.score(posting, profile_summary=profile_summary)
                if llm_result is not None:
                    # Corrections first, so the cached posting and the score
                    # both reflect the same facts.
                    posting = apply_patches(posting, llm_result.patches)
                    # The model answers 0-100; the rest of CareerOS works in
                    # 0.0-1.0, and the two must stay comparable.
                    score = llm_result.score / 100.0

            # Cache the full posting so generation/submission can read it
            # back by URL instead of re-crawling every provider.
            if self._postings is not None:
                self._postings.save(posting)
            application = Application(
                job_title=posting.title,
                company_name=posting.company_name,
                job_url=posting.url,
                source_provider=posting.source_provider,
                match_score=score,
            )

            self._bus.publish(
                Event(
                    event_type="job.scored",
                    source=posting.source_provider,
                    payload={"subject_id": application.id, "job_url": posting.url, "score": score},
                )
            )

            brain.applications.append(application)
            new_applications.append(application)

            self._bus.publish(
                Event(
                    event_type="application.created",
                    source=posting.source_provider,
                    payload={
                        "subject_id": application.id,
                        "job_title": application.job_title,
                        "company_name": application.company_name,
                        "match_score": score,
                    },
                )
            )

        if new_applications:
            self._repository.save(brain)

        return DiscoveryRun(applications=new_applications, source_errors=result.source_errors)
