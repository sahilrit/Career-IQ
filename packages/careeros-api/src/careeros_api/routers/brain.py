"""Career Brain read endpoints — proves the tenant-scoped stack end to
end. Writes and the rest of the surface arrive in later phases."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import ValidationError

from careeros_api.dependencies import Context
from careeros_api.schemas import (
    AwardCreateRequest,
    BrainCreateRequest,
    CertificationCreateRequest,
    EducationCreateRequest,
    ExperienceCreateRequest,
    LanguageCreateRequest,
    PreferencesUpdateRequest,
    ProjectCreateRequest,
    SkillCreateRequest,
    SummaryUpdateRequest,
)
from careeros_career_brain import CareerBrain, CareerBrainRepository, parse_resume_pdf
from careeros_career_brain.models import (
    Award,
    Certification,
    Education,
    Experience,
    Identity,
    Language,
    Preferences,
    Project,
    Skill,
)
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


@router.post("/brain/education", status_code=status.HTTP_201_CREATED)
def add_education(body: EducationCreateRequest, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    brain = _primary(context)
    brain.education.append(
        _build_or_422(
            lambda: Education(
                institution=body.institution,
                credential=body.credential,
                field_of_study=body.field_of_study,
                start_date=_parse_date(body.start_date, "start_date") if body.start_date else None,
                end_date=_parse_date(body.end_date, "end_date") if body.end_date else None,
            )
        )
    )
    CareerBrainRepository(context.store).save(brain)
    return brain.model_dump(mode="json")


@router.delete("/brain/education/{education_id}")
def remove_education(education_id: str, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    brain = _primary(context)
    remaining = [item for item in brain.education if item.id != education_id]
    if len(remaining) == len(brain.education):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "education entry not found")
    brain.education = remaining
    CareerBrainRepository(context.store).save(brain)
    return brain.model_dump(mode="json")


@router.post("/brain/certifications", status_code=status.HTTP_201_CREATED)
def add_certification(body: CertificationCreateRequest, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    brain = _primary(context)
    brain.certifications.append(
        _build_or_422(
            lambda: Certification(
                name=body.name,
                issuer=body.issuer,
                issued_date=_parse_date(body.issued_date, "issued_date")
                if body.issued_date
                else None,
                credential_url=body.credential_url,
            )
        )
    )
    CareerBrainRepository(context.store).save(brain)
    return brain.model_dump(mode="json")


@router.delete("/brain/certifications/{certification_id}")
def remove_certification(certification_id: str, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    brain = _primary(context)
    remaining = [item for item in brain.certifications if item.id != certification_id]
    if len(remaining) == len(brain.certifications):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "certification not found")
    brain.certifications = remaining
    CareerBrainRepository(context.store).save(brain)
    return brain.model_dump(mode="json")


@router.post("/brain/projects", status_code=status.HTTP_201_CREATED)
def add_project(body: ProjectCreateRequest, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    brain = _primary(context)
    brain.projects.append(
        _build_or_422(lambda: Project(name=body.name, description=body.description, url=body.url))
    )
    CareerBrainRepository(context.store).save(brain)
    return brain.model_dump(mode="json")


@router.delete("/brain/projects/{project_id}")
def remove_project(project_id: str, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    brain = _primary(context)
    remaining = [item for item in brain.projects if item.id != project_id]
    if len(remaining) == len(brain.projects):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found")
    brain.projects = remaining
    CareerBrainRepository(context.store).save(brain)
    return brain.model_dump(mode="json")


@router.post("/brain/languages", status_code=status.HTTP_201_CREATED)
def add_language(body: LanguageCreateRequest, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    brain = _primary(context)
    brain.languages.append(
        _build_or_422(lambda: Language(name=body.name, proficiency=body.proficiency))
    )
    CareerBrainRepository(context.store).save(brain)
    return brain.model_dump(mode="json")


@router.delete("/brain/languages/{language_id}")
def remove_language(language_id: str, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    brain = _primary(context)
    remaining = [item for item in brain.languages if item.id != language_id]
    if len(remaining) == len(brain.languages):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "language not found")
    brain.languages = remaining
    CareerBrainRepository(context.store).save(brain)
    return brain.model_dump(mode="json")


@router.post("/brain/awards", status_code=status.HTTP_201_CREATED)
def add_award(body: AwardCreateRequest, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    brain = _primary(context)
    brain.awards.append(_build_or_422(lambda: Award(title=body.title, issuer=body.issuer)))
    CareerBrainRepository(context.store).save(brain)
    return brain.model_dump(mode="json")


@router.delete("/brain/awards/{award_id}")
def remove_award(award_id: str, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    brain = _primary(context)
    remaining = [item for item in brain.awards if item.id != award_id]
    if len(remaining) == len(brain.awards):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "award not found")
    brain.awards = remaining
    CareerBrainRepository(context.store).save(brain)
    return brain.model_dump(mode="json")


@router.delete("/brain/skills/{skill_id}")
def remove_skill(skill_id: str, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    brain = _primary(context)
    remaining = [skill for skill in brain.skills if skill.id != skill_id]
    if len(remaining) == len(brain.skills):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "skill not found")
    brain.skills = remaining
    CareerBrainRepository(context.store).save(brain)
    return brain.model_dump(mode="json")


@router.delete("/brain/experience/{experience_id}")
def remove_experience(experience_id: str, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    brain = _primary(context)
    remaining = [exp for exp in brain.experiences if exp.id != experience_id]
    if len(remaining) == len(brain.experiences):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "experience not found")
    brain.experiences = remaining
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

    if not any(
        (
            parsed.full_name,
            parsed.email,
            parsed.skills,
            parsed.experiences,
            parsed.education,
            parsed.certifications,
        )
    ):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "couldn't find a name, email, skills, experience, or education in that résumé",
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

    # Re-import replaces only the previously résumé-sourced roles — anything the
    # user typed by hand ("manual") is kept. Then merge the fresh parse, deduped
    # against remaining entries so an import never duplicates a manual role.
    if parsed.experiences:
        brain.experiences = [exp for exp in brain.experiences if exp.source != "resume"]
    existing_exp = {
        (exp.title.strip().lower(), exp.company_name.strip().lower()) for exp in brain.experiences
    }
    added_experiences = 0
    for parsed_exp in parsed.experiences:
        key = (parsed_exp.title.strip().lower(), parsed_exp.company.strip().lower())
        if key in existing_exp:
            continue
        brain.experiences.append(
            Experience(
                company_name=parsed_exp.company or "Unknown",
                title=parsed_exp.title,
                start_date=parsed_exp.start_date,
                end_date=parsed_exp.end_date,
                description=parsed_exp.description,
                source="resume",
            )
        )
        existing_exp.add(key)
        added_experiences += 1

    # Education & certifications — same replace-résumé-sourced / keep-manual rule.
    added_education = 0
    if parsed.education:
        brain.education = [item for item in brain.education if item.source != "resume"]
        existing_edu = {
            (item.institution.strip().lower(), item.credential.strip().lower())
            for item in brain.education
        }
        for parsed_edu in parsed.education:
            key = (parsed_edu.institution.strip().lower(), parsed_edu.credential.strip().lower())
            if key in existing_edu:
                continue
            brain.education.append(
                Education(
                    institution=parsed_edu.institution or "Unknown",
                    credential=parsed_edu.credential,
                    end_date=parsed_edu.end_date,
                    source="resume",
                )
            )
            existing_edu.add(key)
            added_education += 1

    added_certifications = 0
    if parsed.certifications:
        brain.certifications = [item for item in brain.certifications if item.source != "resume"]
        existing_cert = {
            (item.name.strip().lower(), (item.issuer or "").strip().lower())
            for item in brain.certifications
        }
        for parsed_cert in parsed.certifications:
            key = (parsed_cert.name.strip().lower(), (parsed_cert.issuer or "").strip().lower())
            if key in existing_cert:
                continue
            brain.certifications.append(
                Certification(name=parsed_cert.name, issuer=parsed_cert.issuer, source="resume")
            )
            existing_cert.add(key)
            added_certifications += 1

    repository.save(brain)
    return {
        "brain": brain.model_dump(mode="json"),
        "imported": {
            "fields": filled,
            "skills_added": added_skills,
            "experiences_added": added_experiences,
            "education_added": added_education,
            "certifications_added": added_certifications,
        },
    }
