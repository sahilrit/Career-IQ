"""Plan definitions: the roadmap's three tiers, as real, checkable
data rather than a marketing description — this is the whole
monetization layer's source of truth for what each tier actually
includes.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class PlanTier(StrEnum):
    FREE = "free"
    PRO = "pro"
    AGENCY = "agency"


class Plan(BaseModel):
    tier: PlanTier
    name: str
    monthly_price_usd: float
    features: list[str]
    max_workspaces: int
    max_team_members: int


PLANS: dict[PlanTier, Plan] = {
    PlanTier.FREE: Plan(
        tier=PlanTier.FREE,
        name="Free",
        monthly_price_usd=0.0,
        features=["career_brain", "basic_opportunity_discovery", "basic_applications"],
        max_workspaces=1,
        max_team_members=1,
    ),
    PlanTier.PRO: Plan(
        tier=PlanTier.PRO,
        name="Pro",
        monthly_price_usd=29.0,
        features=[
            "career_brain",
            "basic_opportunity_discovery",
            "basic_applications",
            "autonomous_workflows",
            "advanced_research",
            "freelance_acquisition",
            "interview_intelligence",
            "analytics",
        ],
        max_workspaces=1,
        max_team_members=1,
    ),
    PlanTier.AGENCY: Plan(
        tier=PlanTier.AGENCY,
        name="Agency / Business",
        monthly_price_usd=99.0,
        features=[
            "career_brain",
            "basic_opportunity_discovery",
            "basic_applications",
            "autonomous_workflows",
            "advanced_research",
            "freelance_acquisition",
            "interview_intelligence",
            "analytics",
            "multiple_workspaces",
            "team_members",
            "advanced_automation",
            "custom_plugins",
            "api_access",
            "enterprise_controls",
        ],
        max_workspaces=10,
        max_team_members=25,
    ),
}


def get_plan(tier: PlanTier) -> Plan:
    return PLANS[tier]
