"""Offer endpoints: add offers and rank them by Opportunity Value."""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from careeros_api.benchmark_support import compensation_benchmark
from careeros_api.dependencies import Context
from careeros_api.schemas import OfferCreateRequest, RankedOfferResponse
from careeros_career_brain import CareerBrainRepository
from careeros_offer_negotiation import Offer, OfferNegotiationDivision, OfferRepository

router = APIRouter(prefix="/offers", tags=["offers"])


class BenchmarkRequest(BaseModel):
    role: str = Field(min_length=1)
    level: str | None = None  # entry | mid | senior | lead
    anchor_salary: int | None = None


def _division(context: Context) -> OfferNegotiationDivision:
    return OfferNegotiationDivision(OfferRepository(context.store))


def _years_experience(brain) -> float:
    """Total years across experiences (open-ended roles count to today)."""
    total_days = 0
    for exp in brain.experiences:
        end = exp.end_date or date.today()
        total_days += max(0, (end - exp.start_date).days)
    return round(total_days / 365.25, 1)


@router.get("", response_model=list[RankedOfferResponse])
def list_offers(context: Context) -> list[RankedOfferResponse]:
    return [
        RankedOfferResponse(
            company_name=row.offer.company_name,
            job_title=row.offer.job_title,
            base_salary=row.offer.base_salary,
            opportunity_value=row.breakdown.opportunity_value,
        )
        for row in _division(context).compare_all()
    ]


@router.post("/benchmark")
def benchmark(body: BenchmarkRequest, context: Context) -> dict[str, Any]:
    """A transparent compensation estimate for a target role — grounded in the
    Career Brain (years of experience, min-salary, currency). Not market data."""
    brains = CareerBrainRepository(context.store).list_all()
    brain = brains[0] if brains else None
    years = _years_experience(brain) if brain else 0.0
    prefs = brain.preferences if brain else None
    return compensation_benchmark(
        role=body.role,
        level=body.level,
        years_experience=years,
        anchor_salary=body.anchor_salary,
        min_salary=prefs.min_salary if prefs else None,
        currency=(prefs.salary_currency if prefs else None) or "USD",
    )


@router.post("", response_model=list[RankedOfferResponse], status_code=status.HTTP_201_CREATED)
def add_offer(body: OfferCreateRequest, context: Context) -> list[RankedOfferResponse]:
    _division(context).add_offer(
        Offer(
            company_name=body.company_name,
            job_title=body.job_title,
            base_salary=body.base_salary,
            bonus=body.bonus,
            equity_value=body.equity_value,
            benefits_value=body.benefits_value,
            remote_policy=body.remote_policy,
            stability_score=body.stability_score,
            growth_score=body.growth_score,
            reputation_score=body.reputation_score,
        )
    )
    return list_offers(context)
