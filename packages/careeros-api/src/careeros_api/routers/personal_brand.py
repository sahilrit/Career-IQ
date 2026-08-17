"""Personal Brand: turn a Career Brain project into publish-ready content
(case study, LinkedIn post, X thread, portfolio page, blog post)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from careeros_api.dependencies import Context
from careeros_career_brain import CareerBrainRepository
from careeros_personal_brand import (
    ContentProgressRepository,
    PersonalBrandDivision,
    TestimonialRepository,
)

router = APIRouter(prefix="/personal-brand", tags=["personal-brand"])


class GenerateContentRequest(BaseModel):
    project_id: str = Field(min_length=1)


def _brain(context: Context):
    brains = CareerBrainRepository(context.store).list_all()
    if not brains:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "create a Career Brain first")
    return brains[0]


def _division(context: Context) -> PersonalBrandDivision:
    return PersonalBrandDivision(
        ContentProgressRepository(context.store), TestimonialRepository(context.store)
    )


@router.get("/projects")
def list_projects(context: Context) -> list[dict[str, Any]]:
    brain = _brain(context)
    return [{"id": project.id, "name": project.name} for project in brain.projects]


@router.post("/generate")
def generate(body: GenerateContentRequest, context: Context) -> dict[str, Any]:
    brain = _brain(context)
    project = next((p for p in brain.projects if p.id == body.project_id), None)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no project with that id")

    division = _division(context)
    case_study = division.generate_case_study(brain, project)
    return {
        "case_study": {
            "title": case_study.title,
            "problem": case_study.problem,
            "approach": case_study.approach,
            "result": case_study.result,
        },
        "linkedin": division.generate_linkedin_post(case_study),
        "x_thread": division.generate_x_thread(case_study),
        "portfolio": division.generate_portfolio_page(case_study, project),
        "blog": division.generate_blog_post(case_study),
    }
