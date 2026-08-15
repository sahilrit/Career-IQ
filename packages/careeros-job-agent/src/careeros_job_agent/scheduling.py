"""Wires a JobAgent onto a Runtime as a recurring job, for 24/7 operation."""

from __future__ import annotations

from datetime import datetime

from careeros_job_agent.agent import JobAgent
from careeros_job_providers import JobSearchQuery
from careeros_runtime import Runtime

DEFAULT_JOB_NAME = "job-agent-cycle"


def register_job_agent(
    runtime: Runtime,
    agent: JobAgent,
    identity_id: str,
    query: JobSearchQuery,
    *,
    interval_seconds: float = 3600,
    job_name: str = DEFAULT_JOB_NAME,
    start_at: datetime | None = None,
) -> None:
    """Register ``agent.run_cycle`` to run on ``runtime`` every ``interval_seconds``."""
    runtime.register_recurring(
        job_name,
        interval_seconds,
        lambda: agent.run_cycle(identity_id, query),
        start_at=start_at,
    )
