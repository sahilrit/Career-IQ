"""Shared runtime context every CLI command builds from a data directory.

Wires together the same objects a scheduled Runtime job would use
(Phases 4-10), so the CLI exercises the real pipeline rather than a
parallel implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from careeros_arbeitnow_provider import ArbeitnowProvider
from careeros_career_brain import CareerBrainRepository
from careeros_common import DocumentStore
from careeros_event_bus import EventBus
from careeros_job_agent import JobAgent
from careeros_job_discovery import JobDiscoveryPipeline
from careeros_job_providers import JobProviderRegistry
from careeros_memory import HistoryLog, attach_history_logging
from careeros_remoteok_provider import RemoteOKProvider


@dataclass
class CLIContext:
    store: DocumentStore
    repository: CareerBrainRepository
    event_bus: EventBus
    history_log: HistoryLog
    provider_registry: JobProviderRegistry
    pipeline: JobDiscoveryPipeline
    agent: JobAgent


def build_context(
    data_dir: str | Path, *, provider_registry: JobProviderRegistry | None = None
) -> CLIContext:
    db_path = Path(data_dir) / "careeros.db"
    store = DocumentStore(db_path)
    repository = CareerBrainRepository(store)
    event_bus = EventBus()
    history_log = HistoryLog(store)
    attach_history_logging(event_bus, history_log)

    if provider_registry is None:
        provider_registry = JobProviderRegistry()
        provider_registry.register(RemoteOKProvider())
        provider_registry.register(ArbeitnowProvider())

    pipeline = JobDiscoveryPipeline(provider_registry, repository, event_bus)
    agent = JobAgent(pipeline, repository, event_bus)

    return CLIContext(
        store=store,
        repository=repository,
        event_bus=event_bus,
        history_log=history_log,
        provider_registry=provider_registry,
        pipeline=pipeline,
        agent=agent,
    )
