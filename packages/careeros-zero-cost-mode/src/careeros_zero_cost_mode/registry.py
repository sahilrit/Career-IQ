"""ZeroCostRegistry: tracks which providers exist for each capability
and whether at least one of them is genuinely free — the mechanism
that makes "no mandatory paid API" checkable rather than just asserted
in documentation.
"""

from __future__ import annotations

from careeros_zero_cost_mode.provider_declaration import CostTier, ProviderDeclaration

_FREE_TIERS = frozenset({CostTier.FREE, CostTier.FREEMIUM})


class ZeroCostRegistry:
    def __init__(self) -> None:
        self._declarations: list[ProviderDeclaration] = []

    def register(self, declaration: ProviderDeclaration) -> None:
        self._declarations.append(declaration)

    def providers_for_capability(self, capability_name: str) -> list[ProviderDeclaration]:
        return [d for d in self._declarations if d.capability_name == capability_name]

    def has_free_path(self, capability_name: str) -> bool:
        return any(
            declaration.cost_tier in _FREE_TIERS
            for declaration in self.providers_for_capability(capability_name)
        )

    def capabilities(self) -> set[str]:
        return {declaration.capability_name for declaration in self._declarations}
