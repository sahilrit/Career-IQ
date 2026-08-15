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

from careeros_career_brain import Application, CareerBrainRepository
from careeros_event_bus import Event, EventBus
from careeros_job_discovery.scoring import score_posting
from careeros_job_providers import JobProviderRegistry, JobSearchQuery


class JobDiscoveryPipeline:
    def __init__(
        self,
        provider_registry: JobProviderRegistry,
        career_brain_repository: CareerBrainRepository,
        event_bus: EventBus,
    ) -> None:
        self._providers = provider_registry
        self._repository = career_brain_repository
        self._bus = event_bus

    def run(self, identity_id: str, query: JobSearchQuery) -> list[Application]:
        """Discover, score, and store new applications for one user's Career Brain.

        Postings already recorded (matched by job URL) are skipped, so
        running this repeatedly only ever adds genuinely new opportunities.
        """
        brain = self._repository.load(identity_id)
        result = self._providers.search_all(query)

        new_applications: list[Application] = []
        for posting in result.postings:
            if brain.find_application_by_job_url(posting.url) is not None:
                continue

            self._bus.publish(
                Event(
                    event_type="job.discovered",
                    source=posting.source_provider,
                    payload={"job_url": posting.url, "title": posting.title},
                )
            )

            score = score_posting(posting, brain)
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

        return new_applications
