"""Interview prep: tailored questions + a one-page briefing, generated from
the Career Brain (stateless — nothing stored)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from careeros_api.dependencies import Context
from careeros_career_brain import CareerBrainRepository
from careeros_interview_intelligence import (
    generate_one_page_briefing,
    generate_questions,
    render_one_page_briefing,
)

router = APIRouter(prefix="/interview", tags=["interview"])


class InterviewPrepRequest(BaseModel):
    job_title: str = Field(min_length=1)
    company_name: str = Field(min_length=1)
    job_description: str = ""


def _brain(context: Context):
    brains = CareerBrainRepository(context.store).list_all()
    if not brains:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "create a Career Brain first")
    return brains[0]


@router.post("/prep")
def prep(body: InterviewPrepRequest, context: Context) -> dict[str, Any]:
    brain = _brain(context)
    questions = generate_questions(
        brain,
        job_title=body.job_title,
        company_name=body.company_name,
        job_description=body.job_description,
    )
    briefing = generate_one_page_briefing(
        brain,
        job_title=body.job_title,
        company_name=body.company_name,
        job_description=body.job_description,
    )
    return {
        "questions": {
            "role_specific": questions.role_specific,
            "technical": questions.technical,
            "company_specific": questions.company_specific,
            "star_prompts": [
                {
                    "question": prompt.question,
                    "achievement_description": prompt.achievement_description,
                    "metric": prompt.metric,
                }
                for prompt in questions.star_prompts
            ],
        },
        "briefing": {
            "company_name": briefing.company_name,
            "job_title": briefing.job_title,
            "strongest_achievements": briefing.strongest_achievements,
            "questions_to_ask": briefing.questions_to_ask,
            "compensation_strategy": briefing.compensation_strategy,
            "things_to_avoid": briefing.things_to_avoid,
        },
        "briefing_text": render_one_page_briefing(briefing),
    }
