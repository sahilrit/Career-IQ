"""The platform's own real cost declarations — a genuine audit trail
for the zero-cost claim, not a generic example list. Every entry here
names an actual provider/technology already shipped in earlier phases.
"""

from __future__ import annotations

from careeros_zero_cost_mode.provider_declaration import CostTier, ProviderDeclaration
from careeros_zero_cost_mode.registry import ZeroCostRegistry

DEFAULT_PLATFORM_DECLARATIONS: list[ProviderDeclaration] = [
    ProviderDeclaration(
        capability_name="find_jobs",
        provider_name="remoteok",
        cost_tier=CostTier.FREE,
        notes="RemoteOK's public API — no key required (Phase 7).",
    ),
    ProviderDeclaration(
        capability_name="find_gigs",
        provider_name="fiverr",
        cost_tier=CostTier.FREE,
        notes="Browser-automation-driven, no paid API (Phase 19).",
    ),
    ProviderDeclaration(
        capability_name="semantic_search",
        provider_name="local_tfidf",
        cost_tier=CostTier.FREE,
        notes="Local TF-IDF index — no embeddings API (Phase 5).",
    ),
    ProviderDeclaration(
        capability_name="document_storage",
        provider_name="sqlite",
        cost_tier=CostTier.FREE,
        notes="Python standard library — no hosted database required (Phase 2).",
    ),
    ProviderDeclaration(
        capability_name="secret_encryption",
        provider_name="fernet",
        cost_tier=CostTier.FREE,
        notes="The `cryptography` package — no hosted KMS (Phase 26).",
    ),
    ProviderDeclaration(
        capability_name="browser_automation",
        provider_name="playwright",
        cost_tier=CostTier.FREE,
        notes="Open-source, no paid browser-automation SaaS (Phase 13).",
    ),
    ProviderDeclaration(
        capability_name="pdf_generation",
        provider_name="fpdf2",
        cost_tier=CostTier.FREE,
        notes="Pure Python, no paid document API (Phase 32).",
    ),
    ProviderDeclaration(
        capability_name="dashboard_ui",
        provider_name="streamlit",
        cost_tier=CostTier.FREE,
        notes="Open-source, self-hosted — no paid hosting required (Phase 43).",
    ),
]


def load_default_registry() -> ZeroCostRegistry:
    registry = ZeroCostRegistry()
    for declaration in DEFAULT_PLATFORM_DECLARATIONS:
        registry.register(declaration)
    return registry
