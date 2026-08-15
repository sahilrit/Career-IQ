"""Freelance funnel: leads, outreach, proposals, calls, clients, and
revenue, read from Phase 31's real per-company pipeline progress and
Phase 37's real income records. "Cold emails sent" maps to the
OUTREACH stage — that's the same generate_outreach step the roadmap
means by it.
"""

from __future__ import annotations

from pydantic import BaseModel

from careeros_client_acquisition import (
    ClientAcquisitionProgressRepository,
    ClientAcquisitionStage,
    Company,
)
from careeros_financial_intelligence import IncomeRecord, IncomeSource

_REVENUE_SOURCES = frozenset({IncomeSource.FREELANCE, IncomeSource.CLIENT_REVENUE})


class FreelanceFunnelMetrics(BaseModel):
    lead_count: int
    outreach_count: int
    proposal_count: int
    call_count: int
    client_count: int
    total_revenue: float


def compute_freelance_funnel(
    companies: list[Company],
    progress_repository: ClientAcquisitionProgressRepository,
    income_records: list[IncomeRecord],
) -> FreelanceFunnelMetrics:
    def reached(company: Company, stage: ClientAcquisitionStage) -> bool:
        return stage in progress_repository.load(company.id).completed_stages

    return FreelanceFunnelMetrics(
        lead_count=len(companies),
        outreach_count=sum(1 for c in companies if reached(c, ClientAcquisitionStage.OUTREACH)),
        proposal_count=sum(1 for c in companies if reached(c, ClientAcquisitionStage.PROPOSAL)),
        call_count=sum(1 for c in companies if reached(c, ClientAcquisitionStage.CALL)),
        client_count=sum(1 for c in companies if reached(c, ClientAcquisitionStage.CLIENT)),
        total_revenue=sum(
            record.amount for record in income_records if record.source in _REVENUE_SOURCES
        ),
    )
