"""Normalized gig posting + search query models shared by every
freelance provider.

Mirrors careeros_job_providers' JobPosting/JobSearchQuery pattern
(Phase 6) for freelance marketplaces. Phase 20 introduces a unifying
Opportunity abstraction on top of both; until then each provider family
keeps its own domain-appropriate shape (a gig has a budget and a client,
not a salary and a company).
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ProjectType(StrEnum):
    FIXED_PRICE = "fixed_price"
    HOURLY = "hourly"


class Budget(BaseModel):
    min_amount: int | None = None
    max_amount: int | None = None
    currency: str = "USD"
    project_type: ProjectType = ProjectType.FIXED_PRICE

    def midpoint(self) -> int | None:
        if self.min_amount is not None and self.max_amount is not None:
            return (self.min_amount + self.max_amount) // 2
        return self.min_amount if self.min_amount is not None else self.max_amount


class GigPosting(BaseModel):
    source_provider: str
    external_id: str
    title: str
    client_name: str
    url: str
    budget: Budget | None = None
    skills_required: list[str] = Field(default_factory=list)
    description: str = ""
    posted_at: datetime | None = None

    @property
    def dedupe_key(self) -> tuple[str, str]:
        return (self.source_provider, self.external_id)


class GigSearchQuery(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    min_budget: int | None = None
    project_types: list[ProjectType] = Field(default_factory=list)
    limit: int = 25
    page: int = 1
