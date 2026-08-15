"""Opportunity: the unifying shape both employment and freelance
postings map into.

    "Find jobs" -> "Find opportunities"

Nothing downstream (scoring, CRM, analytics) needs to know whether an
Opportunity came from a job board or a freelance marketplace — it just
needs title/organization/compensation/tags/description, which both
``JobPosting`` (Phase 6) and ``GigPosting`` (Phase 18) already carry,
just under different field names.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_freelance_providers import GigPosting
from careeros_job_providers import JobPosting


class OpportunityKind(StrEnum):
    EMPLOYMENT = "employment"
    FREELANCE = "freelance"


class Opportunity(BaseModel):
    kind: OpportunityKind
    source_provider: str
    external_id: str
    title: str
    organization_name: str
    url: str
    compensation_amount: int | None = None
    tags: list[str] = Field(default_factory=list)
    description: str = ""
    posted_at: datetime | None = None

    @property
    def dedupe_key(self) -> tuple[str, str, str]:
        return (self.kind.value, self.source_provider, self.external_id)


def from_job_posting(posting: JobPosting) -> Opportunity:
    return Opportunity(
        kind=OpportunityKind.EMPLOYMENT,
        source_provider=posting.source_provider,
        external_id=posting.external_id,
        title=posting.title,
        organization_name=posting.company_name,
        url=posting.url,
        compensation_amount=posting.salary.midpoint() if posting.salary else None,
        tags=list(posting.tags),
        description=posting.description,
        posted_at=posting.posted_at,
    )


def from_gig_posting(posting: GigPosting) -> Opportunity:
    return Opportunity(
        kind=OpportunityKind.FREELANCE,
        source_provider=posting.source_provider,
        external_id=posting.external_id,
        title=posting.title,
        organization_name=posting.client_name,
        url=posting.url,
        compensation_amount=posting.budget.midpoint() if posting.budget else None,
        tags=list(posting.skills_required),
        description=posting.description,
        posted_at=posting.posted_at,
    )
