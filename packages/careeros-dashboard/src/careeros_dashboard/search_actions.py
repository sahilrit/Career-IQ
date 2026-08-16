"""Job search + application generation, click-only: the dashboard's
own wiring of the same real pipeline the CLI's ``search`` and
``generate-package`` commands use (careeros_job_agent + RemoteOK/
Arbeitnow providers + careeros_application_engine), so nothing in the
product requires a terminal.
"""

from __future__ import annotations

from careeros_application_engine import ApplicationPackage, build_application_package
from careeros_arbeitnow_provider import ArbeitnowProvider
from careeros_ashby_provider import AshbyProvider
from careeros_career_brain import CareerBrainRepository
from careeros_common import DocumentStore
from careeros_event_bus import EventBus
from careeros_greenhouse_provider import GreenhouseProvider
from careeros_himalayas_provider import HimalayasProvider
from careeros_job_agent import JobAgent
from careeros_job_discovery import JobDiscoveryPipeline
from careeros_job_providers import JobProviderRegistry, JobSearchQuery
from careeros_jobicy_provider import JobicyProvider
from careeros_remoteok_provider import RemoteOKProvider
from careeros_workingnomads_provider import WorkingNomadsProvider


def default_provider_registry() -> JobProviderRegistry:
    registry = JobProviderRegistry()
    registry.register(RemoteOKProvider())
    registry.register(ArbeitnowProvider())
    registry.register(HimalayasProvider())
    registry.register(JobicyProvider())
    registry.register(WorkingNomadsProvider())
    # Greenhouse + Ashby last: their postings link to open application
    # forms (no login/captcha) — the ones the autopilot can actually submit.
    registry.register(GreenhouseProvider())
    registry.register(AshbyProvider())
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
    pipeline = JobDiscoveryPipeline(registry, repository, bus)
    agent = JobAgent(pipeline, repository, bus)
    query = JobSearchQuery(keywords=keywords, remote_only=remote_only, limit=limit)
    return agent.run_cycle(identity_id, query)


def generate_application_for_job(
    store: DocumentStore,
    identity_id: str,
    job_url: str,
    *,
    provider_registry: JobProviderRegistry | None = None,
) -> ApplicationPackage | None:
    brain = CareerBrainRepository(store).load_or_none(identity_id)
    if brain is None:
        return None

    registry = provider_registry or default_provider_registry()
    result = registry.search_all(JobSearchQuery(limit=200))
    posting = next((p for p in result.postings if p.url == job_url), None)
    if posting is None:
        return None

    return build_application_package(brain, posting)
