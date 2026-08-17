"""Career Intelligence: a direction summary and ranked recommendations
(roles, companies, skills, …) synthesized from recorded signals."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from careeros_api.dependencies import Context
from careeros_career_intelligence import (
    CareerIntelligenceDivision,
    RecommendationCategory,
    SignalInput,
    SignalInputRepository,
)

router = APIRouter(prefix="/career-intel", tags=["career-intel"])


class SignalCreateRequest(BaseModel):
    category: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    score: float = 1.0


def _division(context: Context) -> CareerIntelligenceDivision:
    return CareerIntelligenceDivision(SignalInputRepository(context.store))


@router.get("")
def overview(context: Context) -> dict[str, Any]:
    division = _division(context)
    recommendations = division.all_recommendations()
    return {
        "direction_summary": division.career_direction_summary(),
        "recommendations": {
            category.value: [
                {
                    "subject": ranked.subject,
                    "combined_score": ranked.combined_score,
                    "supporting_signal_count": ranked.supporting_signal_count,
                    "sources": ranked.sources,
                }
                for ranked in ranked_list
            ]
            for category, ranked_list in recommendations.items()
            if ranked_list
        },
    }


@router.post("/signals", status_code=status.HTTP_201_CREATED)
def add_signal(body: SignalCreateRequest, context: Context) -> dict[str, Any]:
    try:
        category = RecommendationCategory(body.category)
    except ValueError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "unknown category") from error
    _division(context).record_signal(
        SignalInput(category=category, subject=body.subject, score=body.score, source="web")
    )
    return {"ok": True}
