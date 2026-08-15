"""The CareerBrain aggregate: one user's complete professional identity."""

from __future__ import annotations

from pydantic import BaseModel, Field

from careeros_career_brain.models import (
    Application,
    Award,
    Certification,
    Company,
    Education,
    Experience,
    Goal,
    Identity,
    Language,
    Preferences,
    Project,
    Recruiter,
    Skill,
)


class CareerBrain(BaseModel):
    """A single user's complete Career Brain.

    Single-tenant for now — Phase 25 (SaaS Identity & Multi-Tenancy) adds
    a tenant/workspace boundary around this without changing its shape.
    """

    identity: Identity
    preferences: Preferences = Field(default_factory=Preferences)
    goals: list[Goal] = Field(default_factory=list)
    experiences: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)
    awards: list[Award] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    companies: list[Company] = Field(default_factory=list)
    recruiters: list[Recruiter] = Field(default_factory=list)
    applications: list[Application] = Field(default_factory=list)

    @property
    def current_experience(self) -> Experience | None:
        return next((e for e in self.experiences if e.is_current), None)

    def skill_names(self) -> set[str]:
        """Lowercased skill names, for cheap membership checks during matching."""
        return {s.name.lower() for s in self.skills}

    def find_application(self, application_id: str) -> Application | None:
        return next((a for a in self.applications if a.id == application_id), None)

    def find_application_by_job_url(self, job_url: str) -> Application | None:
        return next((a for a in self.applications if a.job_url == job_url), None)
