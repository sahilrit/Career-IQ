"""One autopilot cycle: discover -> qualify -> for every qualified
application, navigate to its real form, fill, submit — autonomously.

Composition of already-shipped pieces: JobAgent (Phase 6) for
discovery/qualification, AutonomyPolicy in FULL_AUTONOMOUS mode
(Phase 21) for authorization and pacing, AutonomousApplicationExecutor
(Phase 22) for the submit loop, and this package's live page analysis
for the two things nothing previously supplied: navigation to the form
and on-the-fly field mapping.

Every outcome (submitted / handed off / skipped, with reason) is
persisted as an ``autopilot_run`` document so the dashboard can show
exactly what the autopilot did while nobody was watching.
"""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from careeros_application_engine import build_application_package
from careeros_application_runner import ApplicationRunner
from careeros_autonomous_execution import AutonomousApplicationExecutor
from careeros_autonomy import (
    AuthorizationEngine,
    AutonomyMode,
    AutonomyPolicy,
    DecisionMemory,
    PacingLimiter,
)
from careeros_autopilot.page_analysis import (
    DEFAULT_PROBLEM_DETECTORS,
    detect_form_mapping,
    prepare_application_page,
)
from careeros_autopilot.resume_file import write_resume_pdf
from careeros_browser import BrowserSession, launch_browser_session
from careeros_career_brain import ApplicationStatus, CareerBrainRepository
from careeros_event_bus import EventBus
from careeros_job_agent import JobAgent
from careeros_job_discovery import JobDiscoveryPipeline
from careeros_job_providers import JobPosting, JobProviderRegistry, JobSearchQuery

RUN_ENTITY_TYPE = "autopilot_run"


def run_autopilot_cycle(
    store: Any,
    *,
    provider_registry: JobProviderRegistry,
    keywords: list[str],
    remote_only: bool = True,
    search_limit: int = 500,
    headless: bool = True,
    seconds_between_actions: float = 10.0,
    work_dir: str | Path = ".careeros/autopilot",
    browser_session: BrowserSession | None = None,
) -> dict[str, Any]:
    """Run one full cycle for the store's Career Brain; returns the
    persisted run report as a dict."""
    repository = CareerBrainRepository(store)
    brains = repository.list_all()
    if not brains:
        raise ValueError("No Career Brain in this workspace — nothing to apply with.")
    brain = brains[0]
    identity_id = brain.identity.id
    bus = EventBus()
    query = JobSearchQuery(keywords=keywords, remote_only=remote_only, limit=search_limit)

    # 1. Discover + qualify (idempotent: already-seen URLs are skipped).
    agent = JobAgent(JobDiscoveryPipeline(provider_registry, repository, bus), repository, bus)
    discovery_summary = agent.run_cycle(identity_id, query)

    # 2. Fresh postings, keyed by URL, so the executor can rebuild packages.
    postings_by_url = {
        posting.url: posting for posting in provider_registry.search_all(query).postings
    }

    def resolve_posting(application: Any) -> JobPosting | None:
        posting = postings_by_url.get(application.job_url)
        if posting is not None:
            return posting
        if not application.job_url:
            return None
        # The posting aged out of the providers' current window; rebuild a
        # minimal one from the stored application so we can still apply.
        return JobPosting(
            source_provider=application.source_provider or "unknown",
            external_id=application.id,
            title=application.job_title,
            company_name=application.company_name,
            url=application.job_url,
            remote=True,
        )

    brain = repository.load(identity_id)
    qualified = [a for a in brain.applications if a.status == ApplicationStatus.QUALIFIED]

    report: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "ran_at": datetime.now(UTC).isoformat(),
        "keywords": keywords,
        "discovered": discovery_summary["discovered"],
        "newly_qualified": discovery_summary["qualified"],
        "qualified_total": len(qualified),
        "submitted": 0,
        "outcomes": [],
    }

    if qualified:
        # 3. A PDF resume for upload fields, rendered from the Career Brain.
        work_path = Path(work_dir)
        resume_path: str | None = None
        sample_posting = next(
            (posting for posting in map(resolve_posting, qualified) if posting is not None), None
        )
        if sample_posting is not None:
            sample_package = build_application_package(brain, sample_posting)
            resume_path = str(
                write_resume_pdf(sample_package.resume_text, work_path / "resume.pdf")
            )

        def paced_prepare(session: BrowserSession, posting: Any) -> str | None:
            # Politeness pacing between site visits. The PacingLimiter
            # REJECTS too-fast actions rather than waiting, which would
            # starve every application after the first in a batch run —
            # so pacing lives here as a real wait and the limiter is off.
            time.sleep(seconds_between_actions)
            return prepare_application_page(session, posting)

        executor = AutonomousApplicationExecutor(
            repository=repository,
            autonomy_policy=AutonomyPolicy(
                mode=AutonomyMode.FULL_AUTONOMOUS,
                engine=AuthorizationEngine(),
                pacing=PacingLimiter(0),
                decision_memory=DecisionMemory(store),
                event_bus=bus,
            ),
            application_runner=ApplicationRunner(screenshot_dir=work_path / "screenshots"),
            event_bus=bus,
            resolve_posting=resolve_posting,
            resolve_form_mapping=lambda application: None,
            prepare_page=paced_prepare,
            resolve_form_mapping_live=lambda session, application: detect_form_mapping(session),
        )

        def execute(session: BrowserSession) -> None:
            run = executor.run_for_identity(
                identity_id,
                session,
                detectors=DEFAULT_PROBLEM_DETECTORS,
                resume_file_path=resume_path,
            )
            applications_by_id = {a.id: a for a in qualified}
            report["submitted"] = run.submitted_count
            report["outcomes"] = [
                {
                    "application_id": outcome.application_id,
                    "job_title": getattr(
                        applications_by_id.get(outcome.application_id), "job_title", "?"
                    ),
                    "company_name": getattr(
                        applications_by_id.get(outcome.application_id), "company_name", "?"
                    ),
                    "submitted": outcome.submitted,
                    "reason": outcome.reason,
                }
                for outcome in run.outcomes
            ]

        if browser_session is not None:
            execute(browser_session)
        else:
            with launch_browser_session(headless=headless) as session:
                execute(session)

    store.put(RUN_ENTITY_TYPE, report["id"], report)
    return report


def list_autopilot_runs(store: Any) -> list[dict[str, Any]]:
    return sorted(store.list(RUN_ENTITY_TYPE), key=lambda run: run["ran_at"], reverse=True)
