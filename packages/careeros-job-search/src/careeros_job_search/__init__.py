"""careeros_job_search: the shared app-composition layer for job
discovery — the default provider registry and the two entry points
(search + application generation) that both the Streamlit dashboard and
the FastAPI backend call, so provider wiring lives in exactly one place.
"""

from __future__ import annotations

from careeros_application_engine import (
    ApplicationPackage,
    CoverLetterGenerator,
    build_application_package,
)
from careeros_arbeitnow_provider import ArbeitnowProvider
from careeros_ashby_provider import AshbyProvider
from careeros_career_brain import CareerBrainRepository
from careeros_common import DocumentStore
from careeros_event_bus import EventBus
from careeros_greenhouse_provider import GreenhouseProvider
from careeros_himalayas_provider import HimalayasProvider
from careeros_job_agent import JobAgent
from careeros_job_discovery import JobDiscoveryPipeline, JobPostingRepository
from careeros_job_providers import JobProviderRegistry, JobSearchQuery
from careeros_jobicy_provider import JobicyProvider
from careeros_lever_provider import LeverProvider
from careeros_remoteok_provider import RemoteOKProvider
from careeros_themuse_provider import TheMuseProvider
from careeros_weworkremotely_provider import WeWorkRemotelyProvider
from careeros_workingnomads_provider import WorkingNomadsProvider

__all__ = [
    "default_provider_registry",
    "generate_application_for_job",
    "search_for_jobs",
]


def default_provider_registry() -> JobProviderRegistry:
    registry = JobProviderRegistry()
    registry.register(RemoteOKProvider())
    registry.register(ArbeitnowProvider())
    registry.register(HimalayasProvider())
    registry.register(JobicyProvider())
    registry.register(WorkingNomadsProvider())
    registry.register(WeWorkRemotelyProvider())
    registry.register(TheMuseProvider())
    # Open-form ATS boards last: their postings link to application forms
    # with no login/captcha — the ones the autopilot can actually submit.
    registry.register(GreenhouseProvider())
    registry.register(AshbyProvider())
    registry.register(LeverProvider())
    return registry


def search_for_jobs(
    store: DocumentStore,
    identity_id: str,
    *,
    keywords: list[str],
    remote_only: bool,
    limit: int,
    provider_registry: JobProviderRegistry | None = None,
) -> dict[str, int]:
    registry = provider_registry or default_provider_registry()
    repository = CareerBrainRepository(store)
    bus = EventBus()
    # Cache discovered postings so generation reads them back by URL
    # instead of re-crawling every provider.
    pipeline = JobDiscoveryPipeline(registry, repository, bus, JobPostingRepository(store))
    agent = JobAgent(pipeline, repository, bus)
    query = JobSearchQuery(keywords=keywords, remote_only=remote_only, limit=limit)
    return agent.run_cycle(identity_id, query)


def generate_application_for_job(
    store: DocumentStore,
    identity_id: str,
    job_url: str,
    *,
    provider_registry: JobProviderRegistry | None = None,
    cover_letter_generator: CoverLetterGenerator | None = None,
) -> ApplicationPackage | None:
    brain = CareerBrainRepository(store).load_or_none(identity_id)
    if brain is None:
        return None

    # Fast path: the posting was cached at discovery time — no crawl needed.
    posting = JobPostingRepository(store).load_or_none(job_url)
    if posting is None:
        # Fallback for postings discovered before caching existed: one crawl.
        registry = provider_registry or default_provider_registry()
        result = registry.search_all(JobSearchQuery(limit=200))
        posting = next((p for p in result.postings if p.url == job_url), None)
    if posting is None:
        return None

    return build_application_package(brain, posting, cover_letter_generator=cover_letter_generator)
