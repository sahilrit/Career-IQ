"""ProviderDeclaration: a provider's own statement of what it costs to
run — separate from Phase 24's CapabilityMarketplace (which ranks and
calls providers), since ranking/fallback and cost auditing are
different concerns. A provider still registers with the marketplace to
actually be called; it registers here to be counted toward the
platform's zero-cost guarantee.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class CostTier(StrEnum):
    # No cost to use at all — open-source, local, or a free public API.
    FREE = "free"
    # Free tier exists and is sufficient for core functionality; paid tier optional.
    FREEMIUM = "freemium"
    # Requires a paid account or API key to function at all.
    PAID = "paid"


class ProviderDeclaration(BaseModel):
    capability_name: str
    provider_name: str
    cost_tier: CostTier
    requires_credentials: bool = False
    notes: str = ""
