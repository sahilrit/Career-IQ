"""CapabilityRegistry: a generic register/lookup mechanism for named
capabilities (e.g. "FIND_JOBS", "FIND_GIGS", "SEND_EMAIL").

Phases 6 and 18 each hand-rolled a bespoke registry class
(JobProviderRegistry, FreelanceProviderRegistry) for one capability.
This generalizes that pattern so a new capability doesn't need a new
registry class — Phase 24 builds ranking/fallback/aggregation on top of
this same mechanism.
"""

from __future__ import annotations

from typing import Any


class CapabilityRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, dict[str, Any]] = {}

    def register(self, capability: str, provider_id: str, provider: Any) -> None:
        self._providers.setdefault(capability, {})[provider_id] = provider

    def unregister(self, capability: str, provider_id: str) -> None:
        self._providers.get(capability, {}).pop(provider_id, None)

    def get(self, capability: str, provider_id: str) -> Any | None:
        return self._providers.get(capability, {}).get(provider_id)

    def list_providers(self, capability: str) -> list[Any]:
        return list(self._providers.get(capability, {}).values())

    def list_capabilities(self) -> list[str]:
        return list(self._providers.keys())
