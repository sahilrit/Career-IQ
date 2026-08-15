"""ZeroCostDivision: the facade tying the provider registry, mode
report, and workspace dependency audit together — pre-seeded with the
platform's own real declarations so a fresh instance already reflects
what's actually shipped.
"""

from __future__ import annotations

from pathlib import Path

from careeros_zero_cost_mode.dependency_audit import (
    read_workspace_dependencies,
    scan_dependencies,
)
from careeros_zero_cost_mode.mode_report import (
    ZeroCostModeReport,
    enforce_zero_cost_mode,
    verify_zero_cost_mode,
)
from careeros_zero_cost_mode.platform_declarations import load_default_registry
from careeros_zero_cost_mode.provider_declaration import ProviderDeclaration
from careeros_zero_cost_mode.registry import ZeroCostRegistry


class ZeroCostDivision:
    def __init__(self, registry: ZeroCostRegistry | None = None) -> None:
        self._registry = registry or load_default_registry()

    def register_provider(self, declaration: ProviderDeclaration) -> None:
        self._registry.register(declaration)

    def verify(self, required_capabilities: list[str]) -> ZeroCostModeReport:
        return verify_zero_cost_mode(self._registry, required_capabilities)

    def enforce(self, required_capabilities: list[str]) -> None:
        enforce_zero_cost_mode(self._registry, required_capabilities)

    def audit_workspace_dependencies(self, packages_dir: str | Path) -> dict[str, list[str]]:
        return scan_dependencies(read_workspace_dependencies(packages_dir))
