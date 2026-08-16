"""Job search + application generation for the dashboard.

The real wiring now lives in ``careeros_job_search`` (shared with the
FastAPI backend so provider registration isn't duplicated). This module
re-exports it so existing dashboard imports keep working unchanged.
"""

from __future__ import annotations

from careeros_job_search import (
    default_provider_registry,
    generate_application_for_job,
    search_for_jobs,
)

__all__ = [
    "default_provider_registry",
    "generate_application_for_job",
    "search_for_jobs",
]
