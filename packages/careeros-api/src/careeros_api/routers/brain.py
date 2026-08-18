"""Career Brain read endpoints — proves the tenant-scoped stack end to
end. Writes and the rest of the surface arrive in later phases."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import ValidationError

from careeros_api.dependencies import Context
from careeros_api.schemas import (
    BrainCreateRequest,
    ExperienceCreateRequest,
    PreferencesUpdateRequest,
    SkillCreateRequest,
    SummaryUpdateRequest,
)
from careeros_career_brain import CareerBrain, CareerBrainRepository, parse_resume_pdf
from careeros_career_brain.models import Experience, Identity, Preferences, Skill
from careeros_tenancy import Permission

# Guard the upload endpoint: reject anything that isn't a smallish PDF
# before we hand bytes to the parser.
_MAX_RESUME_BYTES = 10 * 1024 * 1024
_PLACEHOLDER_NAMES = {"", "your name"}
_PLACEHOLDER_EMAILS = {"", "you@example.com"}

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


def _build_or_422(factory):
    """Construct a domain model, turning a model-validator rejection (e.g. an
    end date before the start date) into a friendly 422 instead of a bare 500."""
    try:
        return factory()
    except ValidationError as error:
        errors = error.errors()
        message = errors[0].get("msg", "invalid value") if errors else "invalid value"
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, message.removeprefix("Value error, ")
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


@router.patch("/brain/preferences")
def update_preferences(body: PreferencesUpdateRequest, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    brain = _primary(context)
    merged = {**brain.preferences.model_dump(), **body.model_dump(exclude_unset=True)}
    brain.preferences = _build_or_422(lambda: Preferences(**merged))
    CareerBrainRepository(context.store).save(brain)
    return brain.model_dump(mode="json")


@router.post("/brain/skills", status_code=status.HTTP_201_CREATED)
def add_skill(body: SkillCreateRequest, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    brain = _primary(context)
    brain.skills.append(_build_or_422(lambda: Skill(name=body.name, proficiency=body.proficiency)))
    CareerBrainRepository(context.store).save(brain)
    return brain.model_dump(mode="json")


@router.post("/brain/experience", status_code=status.HTTP_201_CREATED)
def add_experience(body: ExperienceCreateRequest, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    brain = _primary(context)
    start_date = _parse_date(body.start_date, "start_date")
    end_date = _parse_date(body.end_date, "end_date") if body.end_date else None
    brain.experiences.append(
        _build_or_422(
            lambda: Experience(
                company_name=body.company_name,
                title=body.title,
                start_date=start_date,
                end_date=end_date,
                description=body.description,
            )
        )
    )
    CareerBrainRepository(context.store).save(brain)
    return brain.model_dump(mode="json")


@router.post("/brain/import-resume", status_code=status.HTTP_200_OK)
async def import_resume(context: Context, file: Annotated[UploadFile, File(...)]) -> dict[str, Any]:
    """Parse an uploaded resume PDF and merge it into the Career Brain.

    Fills only *empty* identity fields (never clobbers what the user
    typed) and adds skills not already present, so it's safe to run over
    an existing brain. Creates a brain if none exists yet.
    """
    context.require_permission(Permission.CAREER_BRAIN_WRITE)

    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "the uploaded file is empty")
    if len(data) > _MAX_RESUME_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "resume must be under 10 MB")
    filename = (file.filename or "").lower()
    if not (filename.endswith(".pdf") or (file.content_type or "").endswith("pdf")):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "please upload a PDF résumé")

    try:
        parsed = parse_resume_pdf(data)
    except Exception as error:  # pypdf raises assorted errors on bad PDFs
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "couldn't read that PDF — try another file"
        ) from error

    if not parsed.full_name and not parsed.email and not parsed.skills:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "couldn't find a name, email, or skills in that résumé",
        )

    repository = CareerBrainRepository(context.store)
    brains = repository.list_all()
    if brains:
        brain = brains[0]
    else:
        brain = CareerBrain(
            identity=Identity(
                full_name=parsed.full_name or "Your Name",
                email=parsed.email or "you@example.com",
            )
        )

    identity = brain.identity
    filled: list[str] = []
    if identity.full_name.strip().lower() in _PLACEHOLDER_NAMES and parsed.full_name:
        identity.full_name = parsed.full_name
        filled.append("name")
    if identity.email.strip().lower() in _PLACEHOLDER_EMAILS and parsed.email:
        identity.email = parsed.email
        filled.append("email")
    if not identity.phone and parsed.phone:
        identity.phone = parsed.phone
        filled.append("phone")
    if not identity.headline and parsed.headline:
        identity.headline = parsed.headline
        filled.append("headline")
    if not identity.summary and parsed.summary:
        identity.summary = parsed.summary
        filled.append("summary")

    existing = {skill.name.strip().lower() for skill in brain.skills}
    added_skills = 0
    for name in parsed.skills:
        if name.strip().lower() not in existing:
            brain.skills.append(Skill(name=name))
            existing.add(name.strip().lower())
            added_skills += 1

    repository.save(brain)
    return {
        "brain": brain.model_dump(mode="json"),
        "imported": {"fields": filled, "skills_added": added_skills},
    }
