"""Company qualification: does this prospect match the Ideal Client
Profile and have enough real, detected problems to be worth pursuing?
Rule-based, deterministic — no scoring model, nothing fabricated.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from careeros_client_acquisition.company import Company
from careeros_client_acquisition.signals import ProblemSignal


class IdealClientProfile(BaseModel):
    industries: list[str] = Field(default_factory=list)
    """Empty means no industry restriction."""
    min_signal_count: int = 1


def qualify(company: Company, signals: list[ProblemSignal], profile: IdealClientProfile) -> bool:
    if profile.industries and company.industry not in profile.industries:
        return False
    return len(signals) >= profile.min_signal_count
