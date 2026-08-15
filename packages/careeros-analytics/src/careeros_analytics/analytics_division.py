"""AnalyticsDivision: the facade computing every metric from the same
DocumentStore every other package writes to — no separate analytics
database, no data duplicated or fabricated, just real-time computation
over what's already there.
"""

from __future__ import annotations

from careeros_analytics.application_funnel import (
    ApplicationFunnelMetrics,
    compute_application_funnel,
)
from careeros_analytics.career_roi import CareerROIBreakdown, compute_career_roi
from careeros_analytics.freelance_funnel import FreelanceFunnelMetrics, compute_freelance_funnel
from careeros_analytics.industry_performance import compute_industry_performance
from careeros_analytics.network_growth import NetworkGrowthMetrics, compute_network_growth
from careeros_analytics.platform_performance import compute_platform_performance
from careeros_career_brain import Application, CareerBrainRepository
from careeros_client_acquisition import ClientAcquisitionProgressRepository, CompanyRepository
from careeros_common import DocumentStore
from careeros_crm import ContactRepository, TimelineRepository
from careeros_financial_intelligence import IncomeRepository
from careeros_offer_negotiation import OfferRepository


class AnalyticsDivision:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def _all_applications(self) -> list[Application]:
        return [
            application
            for brain in CareerBrainRepository(self._store).list_all()
            for application in brain.applications
        ]

    def application_funnel(self) -> ApplicationFunnelMetrics:
        return compute_application_funnel(self._all_applications())

    def platform_performance(self) -> dict[str, ApplicationFunnelMetrics]:
        return compute_platform_performance(self._all_applications())

    def industry_performance(self) -> dict[str, int]:
        return compute_industry_performance(CompanyRepository(self._store).list_all())

    def freelance_funnel(self) -> FreelanceFunnelMetrics:
        return compute_freelance_funnel(
            CompanyRepository(self._store).list_all(),
            ClientAcquisitionProgressRepository(self._store),
            IncomeRepository(self._store).list_all(),
        )

    def network_growth(self) -> NetworkGrowthMetrics:
        return compute_network_growth(
            ContactRepository(self._store).list_all(), TimelineRepository(self._store)
        )

    def career_roi(self) -> CareerROIBreakdown:
        brains = CareerBrainRepository(self._store).list_all()
        skill_count = len(brains[0].skills) if brains else 0
        return compute_career_roi(
            income_records=IncomeRepository(self._store).list_all(),
            open_offers=OfferRepository(self._store).list_all(),
            network_contact_count=len(ContactRepository(self._store).list_all()),
            skill_count=skill_count,
        )
