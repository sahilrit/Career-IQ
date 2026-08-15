"""Career Brain UI actions: thin wrappers around
careeros_career_brain.CareerBrainRepository that save immediately after
each mutation, so the UI layer never has to remember to call save()
itself and can't accidentally lose an edit.
"""

from __future__ import annotations

from datetime import date

from careeros_career_brain import (
    Achievement,
    Award,
    CareerBrain,
    CareerBrainRepository,
    Certification,
    Education,
    Experience,
    Goal,
    Identity,
    Language,
    Project,
    Skill,
)
from careeros_common import DocumentStore


def get_or_create_brain(store: DocumentStore, *, full_name: str, email: str) -> CareerBrain:
    repository = CareerBrainRepository(store)
    existing = repository.list_all()
    if existing:
        return existing[0]
    brain = CareerBrain(identity=Identity(full_name=full_name, email=email))
    repository.save(brain)
    return brain


def add_skill(store: DocumentStore, brain: CareerBrain, name: str, proficiency: int) -> CareerBrain:
    brain.skills.append(Skill(name=name, proficiency=proficiency))
    CareerBrainRepository(store).save(brain)
    return brain


def add_project(
    store: DocumentStore,
    brain: CareerBrain,
    *,
    name: str,
    description: str = "",
    url: str | None = None,
    skills_used: list[str] | None = None,
) -> CareerBrain:
    brain.projects.append(
        Project(name=name, description=description, url=url, skills_used=skills_used or [])
    )
    CareerBrainRepository(store).save(brain)
    return brain


def add_goal(store: DocumentStore, brain: CareerBrain, description: str) -> CareerBrain:
    brain.goals.append(Goal(description=description))
    CareerBrainRepository(store).save(brain)
    return brain


def add_experience(
    store: DocumentStore,
    brain: CareerBrain,
    *,
    company_name: str,
    title: str,
    start_date: date,
    end_date: date | None = None,
    description: str = "",
) -> CareerBrain:
    brain.experiences.append(
        Experience(
            company_name=company_name,
            title=title,
            start_date=start_date,
            end_date=end_date,
            description=description,
        )
    )
    CareerBrainRepository(store).save(brain)
    return brain


def add_achievement(
    store: DocumentStore,
    brain: CareerBrain,
    experience_id: str,
    *,
    description: str,
    metric: str | None = None,
) -> CareerBrain:
    for experience in brain.experiences:
        if experience.id == experience_id:
            experience.achievements.append(Achievement(description=description, metric=metric))
            break
    CareerBrainRepository(store).save(brain)
    return brain


def update_preferences(
    store: DocumentStore, brain: CareerBrain, *, desired_titles: list[str], remote_only: bool
) -> CareerBrain:
    brain.preferences.desired_titles = desired_titles
    brain.preferences.remote_only = remote_only
    CareerBrainRepository(store).save(brain)
    return brain


def update_summary(store: DocumentStore, brain: CareerBrain, summary: str) -> CareerBrain:
    brain.identity.summary = summary
    CareerBrainRepository(store).save(brain)
    return brain


def add_education(
    store: DocumentStore,
    brain: CareerBrain,
    *,
    institution: str,
    credential: str,
    field_of_study: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    description: str = "",
) -> CareerBrain:
    brain.education.append(
        Education(
            institution=institution,
            credential=credential,
            field_of_study=field_of_study,
            start_date=start_date,
            end_date=end_date,
            description=description,
        )
    )
    CareerBrainRepository(store).save(brain)
    return brain


def add_certification(
    store: DocumentStore,
    brain: CareerBrain,
    *,
    name: str,
    issuer: str | None = None,
    issued_date: date | None = None,
    expiration_date: date | None = None,
    credential_url: str | None = None,
) -> CareerBrain:
    brain.certifications.append(
        Certification(
            name=name,
            issuer=issuer,
            issued_date=issued_date,
            expiration_date=expiration_date,
            credential_url=credential_url,
        )
    )
    CareerBrainRepository(store).save(brain)
    return brain


def add_language(
    store: DocumentStore, brain: CareerBrain, name: str, proficiency: str
) -> CareerBrain:
    brain.languages.append(Language(name=name, proficiency=proficiency))
    CareerBrainRepository(store).save(brain)
    return brain


def add_award(
    store: DocumentStore,
    brain: CareerBrain,
    *,
    title: str,
    issuer: str | None = None,
    date_received: date | None = None,
    description: str = "",
) -> CareerBrain:
    brain.awards.append(
        Award(title=title, issuer=issuer, date_received=date_received, description=description)
    )
    CareerBrainRepository(store).save(brain)
    return brain
