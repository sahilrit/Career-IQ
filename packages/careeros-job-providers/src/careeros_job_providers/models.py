"""Normalized job posting + search query models shared by every provider.

Every provider (RemoteOK today, LinkedIn/Indeed/Wellfound/Naukri behind
future plugins) maps its own API/HTML into these shapes. Nothing
downstream of a provider needs to know which one produced a given
``JobPosting`` — that's the ``FIND_JOBS`` capability abstraction.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class EmploymentType(StrEnum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"


class Salary(BaseModel):
    min_amount: int | None = None
    max_amount: int | None = None
    currency: str = "USD"
    period: str = "year"

    def midpoint(self) -> int | None:
        if self.min_amount is not None and self.max_amount is not None:
            return (self.min_amount + self.max_amount) // 2
        return self.min_amount if self.min_amount is not None else self.max_amount


class JobPosting(BaseModel):
    source_provider: str
    external_id: str
    title: str
    company_name: str
    url: str
    location: str | None = None
    remote: bool = False
    salary: Salary | None = None
    employment_type: EmploymentType | None = None
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    posted_at: datetime | None = None

    @property
    def dedupe_key(self) -> tuple[str, str]:
        return (self.source_provider, self.external_id)


class JobSearchQuery(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    remote_only: bool = False
    min_salary: int | None = None
    employment_types: list[EmploymentType] = Field(default_factory=list)
    limit: int = 25
    page: int = 1
