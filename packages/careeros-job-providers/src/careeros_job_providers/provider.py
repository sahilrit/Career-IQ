"""The provider interface every job-discovery source implements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_job_providers.models import JobPosting, JobSearchQuery

CAPABILITY_FIND_JOBS = "FIND_JOBS"


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class ProviderHealth(BaseModel):
    status: HealthStatus
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    detail: str = ""


class JobSearchResult(BaseModel):
    postings: list[JobPosting] = Field(default_factory=list)
    has_more: bool = False
    next_page: int | None = None


class JobProvider(ABC):
    """A single opportunity source that provides the ``FIND_JOBS`` capability.

    The rest of CareerOS talks to providers only through this interface —
    see ``JobProviderRegistry`` — so RemoteOK (Phase 7) and every provider
    after it are interchangeable from the caller's point of view.
    """

    capability = CAPABILITY_FIND_JOBS

    @property
    @abstractmethod
    def provider_id(self) -> str: ...

    @abstractmethod
    def search(self, query: JobSearchQuery) -> JobSearchResult: ...

    def health_check(self) -> ProviderHealth:
        """Default: assume healthy. Providers with a real probe override this."""
        return ProviderHealth(status=HealthStatus.HEALTHY)
