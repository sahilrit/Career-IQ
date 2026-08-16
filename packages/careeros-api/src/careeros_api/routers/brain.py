"""Career Brain read endpoints — proves the tenant-scoped stack end to
end. Writes and the rest of the surface arrive in later phases."""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, status

from careeros_api.dependencies import Context
from careeros_api.schemas import (
    BrainCreateRequest,
    ExperienceCreateRequest,
    SkillCreateRequest,
    SummaryUpdateRequest,
)
from careeros_career_brain import CareerBrain, CareerBrainRepository
from careeros_career_brain.models import Experience, Identity, Skill
from careeros_tenancy import Permission

router = APIRouter(tags=["brain"])


def _primary(context: Context) -> CareerBrain:
    brains = CareerBrainRepository(context.store).list_all()
    if not brains:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no Career Brain in this workspace")
    return brains[0]


def _parse_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, f"{field} must be an ISO date (YYYY-MM-DD)"
        ) from error


@router.get("/brain")
def get_brain(context: Context) -> dict[str, Any]:
    return _primary(context).model_dump(mode="json")


@router.post("/brain", status_code=status.HTTP_201_CREATED)
def create_brain(body: BrainCreateRequest, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    repository = CareerBrainRepository(context.store)
    if repository.list_all():
        raise HTTPException(status.HTTP_409_CONFLICT, "a Career Brain already exists")
    brain = CareerBrain(identity=Identity(full_name=body.full_name, email=body.email))
    repository.save(brain)
    return brain.model_dump(mode="json")


@router.patch("/brain/summary")
def update_summary(body: SummaryUpdateRequest, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    brain = _primary(context)
    brain.identity.summary = body.summary
    CareerBrainRepository(context.store).save(brain)
    return brain.model_dump(mode="json")


@router.post("/brain/skills", status_code=status.HTTP_201_CREATED)
def add_skill(body: SkillCreateRequest, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    brain = _primary(context)
    brain.skills.append(Skill(name=body.name, proficiency=body.proficiency))
    CareerBrainRepository(context.store).save(brain)
    return brain.model_dump(mode="json")


@router.post("/brain/experience", status_code=status.HTTP_201_CREATED)
def add_experience(body: ExperienceCreateRequest, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    brain = _primary(context)
    brain.experiences.append(
        Experience(
            company_name=body.company_name,
            title=body.title,
            start_date=_parse_date(body.start_date, "start_date"),
            end_date=_parse_date(body.end_date, "end_date") if body.end_date else None,
            description=body.description,
        )
    )
    CareerBrainRepository(context.store).save(brain)
    return brain.model_dump(mode="json")


@router.get("/applications")
def list_applications(context: Context) -> list[dict[str, Any]]:
    return [
        application.model_dump(mode="json")
        for brain in CareerBrainRepository(context.store).list_all()
        for application in brain.applications
    ]
