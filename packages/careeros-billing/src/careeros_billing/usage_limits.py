"""Usage limits: workspace and team-member caps read straight from the
plan definitions — the same source of truth feature gating uses, so a
plan's limits and its features can never disagree.

While open access is on, every workspace is measured against the Agency
caps. Free for all, but still finite.
"""

from __future__ import annotations

from careeros_billing.open_access import effective_tier
from careeros_billing.plan import PlanTier, get_plan


def can_add_workspace(tier: PlanTier, current_workspace_count: int) -> bool:
    return current_workspace_count < get_plan(effective_tier(tier)).max_workspaces


def can_add_team_member(tier: PlanTier, current_team_member_count: int) -> bool:
    return current_team_member_count < get_plan(effective_tier(tier)).max_team_members
