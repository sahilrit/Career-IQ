"""Finding: the shared shape every audit source (baseline website
signals from Phase 31, Shopify-specific, Meta-Ads-specific) normalizes
into, so deliverable generation (Loom script, PDF, email, proposal)
never needs to know which detector produced a given finding.
"""

from __future__ import annotations

from pydantic import BaseModel


class Finding(BaseModel):
    category: str
    detail: str
    recommendation: str
