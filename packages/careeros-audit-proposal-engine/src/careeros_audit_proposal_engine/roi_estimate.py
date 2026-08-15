"""ROI estimation: a transparent, heuristic-based projection of what
fixing the audit's findings could be worth — not a guarantee. Every
number here is derived from figures the prospect (or the freelancer,
from public information) actually supplies; nothing is invented.
"""

from __future__ import annotations

from pydantic import BaseModel

_DEFAULT_UPLIFT_PER_FINDING = 0.02
_DEFAULT_MAX_UPLIFT = 0.30
DISCLAIMER = "Estimate only, based on a simple heuristic — not a guarantee of results."


class ROIInputs(BaseModel):
    monthly_visitors: int
    conversion_rate: float
    average_order_value: float


class ROIEstimate(BaseModel):
    current_monthly_revenue: float
    assumed_uplift_pct: float
    projected_additional_monthly_revenue: float
    projected_additional_annual_revenue: float
    disclaimer: str = DISCLAIMER


def estimate_roi(
    inputs: ROIInputs,
    finding_count: int,
    *,
    uplift_per_finding_pct: float = _DEFAULT_UPLIFT_PER_FINDING,
    max_uplift_pct: float = _DEFAULT_MAX_UPLIFT,
) -> ROIEstimate:
    current_monthly_revenue = (
        inputs.monthly_visitors * inputs.conversion_rate * inputs.average_order_value
    )
    assumed_uplift_pct = min(finding_count * uplift_per_finding_pct, max_uplift_pct)
    additional_monthly = current_monthly_revenue * assumed_uplift_pct
    return ROIEstimate(
        current_monthly_revenue=current_monthly_revenue,
        assumed_uplift_pct=assumed_uplift_pct,
        projected_additional_monthly_revenue=additional_monthly,
        projected_additional_annual_revenue=additional_monthly * 12,
    )
