"""careeros_analytics: Analytics & Career ROI.

Funnel, platform, industry, and network metrics computed from real
data across the platform, plus a transparent Career ROI breakdown.
Resume/proposal performance is Phase 39's Learning Lab
(``careeros_learning_lab.compute_variant_metrics`` scoped to
``ExperimentType.RESUME`` / ``ExperimentType.PROPOSAL``) — not
duplicated here.
"""

from careeros_analytics.analytics_division import AnalyticsDivision
from careeros_analytics.application_funnel import (
    ApplicationFunnelMetrics,
    compute_application_funnel,
)
from careeros_analytics.career_roi import DISCLAIMER, CareerROIBreakdown, compute_career_roi
from careeros_analytics.exceptions import AnalyticsError
from careeros_analytics.freelance_funnel import FreelanceFunnelMetrics, compute_freelance_funnel
from careeros_analytics.industry_performance import compute_industry_performance
from careeros_analytics.network_growth import NetworkGrowthMetrics, compute_network_growth
from careeros_analytics.platform_performance import compute_platform_performance

__all__ = [
    "DISCLAIMER",
    "AnalyticsDivision",
    "AnalyticsError",
    "ApplicationFunnelMetrics",
    "CareerROIBreakdown",
    "FreelanceFunnelMetrics",
    "NetworkGrowthMetrics",
    "compute_application_funnel",
    "compute_career_roi",
    "compute_freelance_funnel",
    "compute_industry_performance",
    "compute_network_growth",
    "compute_platform_performance",
]
