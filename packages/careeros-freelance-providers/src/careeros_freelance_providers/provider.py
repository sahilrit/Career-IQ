"""The provider interface every freelance-opportunity source implements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_freelance_providers.models import GigPosting, GigSearchQuery

CAPABILITY_FIND_GIGS = "FIND_GIGS"


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class ProviderHealth(BaseModel):
    status: HealthStatus
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    detail: str = ""


class GigSearchResult(BaseModel):
    postings: list[GigPosting] = Field(default_factory=list)
    has_more: bool = False
    next_page: int | None = None


class FreelanceProvider(ABC):
    """A single freelance marketplace that provides the ``FIND_GIGS`` capability."""

    capability = CAPABILITY_FIND_GIGS

    @property
    @abstractmethod
    def provider_id(self) -> str: ...

    @abstractmethod
    def search(self, query: GigSearchQuery) -> GigSearchResult: ...

    def health_check(self) -> ProviderHealth:
        """Default: assume healthy. Providers with a real probe override this."""
        return ProviderHealth(status=HealthStatus.HEALTHY)
