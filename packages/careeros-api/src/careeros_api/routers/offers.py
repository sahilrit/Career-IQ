"""Offer endpoints: add offers and rank them by Opportunity Value."""

from __future__ import annotations

from fastapi import APIRouter, status

from careeros_api.dependencies import Context
from careeros_api.schemas import OfferCreateRequest, RankedOfferResponse
from careeros_offer_negotiation import Offer, OfferNegotiationDivision, OfferRepository

router = APIRouter(prefix="/offers", tags=["offers"])


def _division(context: Context) -> OfferNegotiationDivision:
    return OfferNegotiationDivision(OfferRepository(context.store))


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
