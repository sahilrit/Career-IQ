"""Career Brain domain models.

These are the authoritative representation of a user's professional
identity. AI-generated content (a resume, a cover letter, an outreach
message, an autonomous application) is derived FROM these records in
later phases; nothing here is ever invented by an LLM — see
docs/architecture/overview.md's zero-fabrication principle.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator

from careeros_career_brain.exceptions import InvalidStatusTransitionError


def _new_id() -> str:
    return str(uuid.uuid4())


class Identity(BaseModel):
    """Who the user is. One per Career Brain."""

    id: str = Field(default_factory=_new_id)
    full_name: str
    headline: str = ""
    summary: str = ""
    email: str
    phone: str | None = None
    location: str | None = None
    links: dict[str, str] = Field(default_factory=dict)


class Preferences(BaseModel):
    """What the user wants out of their next opportunity."""

    desired_titles: list[str] = Field(default_factory=list)
    desired_locations: list[str] = Field(default_factory=list)
    remote_only: bool = False
    min_salary: int | None = None
    salary_currency: str = "USD"
    employment_types: list[str] = Field(default_factory=list)
    industries_of_interest: list[str] = Field(default_factory=list)
    industries_to_avoid: list[str] = Field(default_factory=list)

    @field_validator("min_salary")
    @classmethod
    def _salary_not_negative(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("min_salary cannot be negative")
        return value


class Goal(BaseModel):
    id: str = Field(default_factory=_new_id)
    description: str
    target_date: date | None = None
    achieved: bool = False


class Skill(BaseModel):
    id: str = Field(default_factory=_new_id)
    name: str
    category: str = "general"
    proficiency: int = Field(default=3, ge=1, le=5)
    years_experience: float | None = Field(default=None, ge=0)


class Achievement(BaseModel):
    id: str = Field(default_factory=_new_id)
    description: str
    metric: str | None = None
    skills_demonstrated: list[str] = Field(default_factory=list)


class Experience(BaseModel):
    id: str = Field(default_factory=_new_id)
    company_name: str
    title: str
    start_date: date
    end_date: date | None = None
    location: str | None = None
    description: str = ""
    achievements: list[Achievement] = Field(default_factory=list)
    skills_used: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _end_not_before_start(self) -> Experience:
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        return self

    @property
    def is_current(self) -> bool:
        return self.end_date is None


class Project(BaseModel):
    id: str = Field(default_factory=_new_id)
    name: str
    description: str = ""
    url: str | None = None
    skills_used: list[str] = Field(default_factory=list)
    start_date: date | None = None
    end_date: date | None = None


class Education(BaseModel):
    id: str = Field(default_factory=_new_id)
    institution: str
    credential: str
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    description: str = ""

    @model_validator(mode="after")
    def _end_not_before_start(self) -> Education:
        has_both_dates = self.start_date is not None and self.end_date is not None
        if has_both_dates and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        return self


class Certification(BaseModel):
    id: str = Field(default_factory=_new_id)
    name: str
    issuer: str | None = None
    issued_date: date | None = None
    expiration_date: date | None = None
    credential_url: str | None = None

    @model_validator(mode="after")
    def _expiration_not_before_issued(self) -> Certification:
        has_both_dates = self.issued_date is not None and self.expiration_date is not None
        if has_both_dates and self.expiration_date < self.issued_date:
            raise ValueError("expiration_date cannot be before issued_date")
        return self


class Language(BaseModel):
    id: str = Field(default_factory=_new_id)
    name: str
    proficiency: str = "conversational"


class Award(BaseModel):
    id: str = Field(default_factory=_new_id)
    title: str
    issuer: str | None = None
    date_received: date | None = None
    description: str = ""


class Company(BaseModel):
    id: str = Field(default_factory=_new_id)
    name: str
    domain: str | None = None
    industry: str | None = None
    size: str | None = None
    notes: str = ""


class Recruiter(BaseModel):
    id: str = Field(default_factory=_new_id)
    full_name: str
    company_id: str | None = None
    email: str | None = None
    linkedin_url: str | None = None
    notes: str = ""


class ApplicationStatus(StrEnum):
    DISCOVERED = "discovered"
    QUALIFIED = "qualified"
    APPLIED = "applied"
    IN_REVIEW = "in_review"
    INTERVIEWING = "interviewing"
    OFFER = "offer"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


# Allowed forward transitions. Terminal states have no outgoing edges. This
# is the domain rule that keeps autonomous status updates (Phase 10+)
# honest about what actually happened, instead of an agent being able to
# jump an application straight from "discovered" to "accepted".
ALLOWED_STATUS_TRANSITIONS: dict[ApplicationStatus, frozenset[ApplicationStatus]] = {
    ApplicationStatus.DISCOVERED: frozenset(
        {ApplicationStatus.QUALIFIED, ApplicationStatus.WITHDRAWN}
    ),
    ApplicationStatus.QUALIFIED: frozenset(
        {ApplicationStatus.APPLIED, ApplicationStatus.WITHDRAWN}
    ),
    ApplicationStatus.APPLIED: frozenset(
        {ApplicationStatus.IN_REVIEW, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN}
    ),
    ApplicationStatus.IN_REVIEW: frozenset(
        {ApplicationStatus.INTERVIEWING, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN}
    ),
    ApplicationStatus.INTERVIEWING: frozenset(
        {ApplicationStatus.OFFER, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN}
    ),
    ApplicationStatus.OFFER: frozenset(
        {ApplicationStatus.ACCEPTED, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN}
    ),
    ApplicationStatus.ACCEPTED: frozenset(),
    ApplicationStatus.REJECTED: frozenset(),
    ApplicationStatus.WITHDRAWN: frozenset(),
}


class StatusChange(BaseModel):
    status: ApplicationStatus
    changed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    note: str = ""


class Application(BaseModel):
    id: str = Field(default_factory=_new_id)
    job_title: str
    company_name: str
    job_url: str | None = None
    source_provider: str | None = None
    status: ApplicationStatus = ApplicationStatus.DISCOVERED
    history: list[StatusChange] = Field(default_factory=list)
    match_score: float | None = Field(default=None, ge=0, le=1)
    resume_id: str | None = None
    cover_letter_id: str | None = None
    notes: str = ""

    @model_validator(mode="after")
    def _seed_history(self) -> Application:
        if not self.history:
            self.history.append(StatusChange(status=self.status))
        return self

    def transition_to(self, new_status: ApplicationStatus, *, note: str = "") -> None:
        """Move to ``new_status``, enforcing ``ALLOWED_STATUS_TRANSITIONS``."""
        allowed = ALLOWED_STATUS_TRANSITIONS[self.status]
        if new_status not in allowed:
            allowed_values = sorted(s.value for s in allowed)
            raise InvalidStatusTransitionError(
                f"Cannot move application from {self.status.value!r} to "
                f"{new_status.value!r}; allowed next states: {allowed_values}"
            )
        self.status = new_status
        self.history.append(StatusChange(status=new_status, note=note))
