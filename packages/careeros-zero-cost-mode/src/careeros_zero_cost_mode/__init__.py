"""careeros_zero_cost_mode: Zero-Cost Infrastructure Mode.

Makes "CareerOS must not depend on paid APIs" an explicit, tested
requirement: a provider cost registry, a workspace dependency audit for
known-paid SDKs, and a mode report/enforcement gate — pre-seeded with
the platform's own real provider declarations (RemoteOK, Fiverr, local
TF-IDF, SQLite, Fernet, Playwright, fpdf2, Streamlit).
"""

from careeros_zero_cost_mode.dependency_audit import (
    read_workspace_dependencies,
    scan_dependencies,
)
from careeros_zero_cost_mode.exceptions import ZeroCostModeError, ZeroCostViolationError
from careeros_zero_cost_mode.mode_report import (
    CapabilityCostStatus,
    ZeroCostModeReport,
    enforce_zero_cost_mode,
    verify_zero_cost_mode,
)
from careeros_zero_cost_mode.platform_declarations import (
    DEFAULT_PLATFORM_DECLARATIONS,
    load_default_registry,
)
from careeros_zero_cost_mode.provider_declaration import CostTier, ProviderDeclaration
from careeros_zero_cost_mode.registry import ZeroCostRegistry
from careeros_zero_cost_mode.zero_cost_division import ZeroCostDivision

__all__ = [
    "DEFAULT_PLATFORM_DECLARATIONS",
    "CapabilityCostStatus",
    "CostTier",
    "ProviderDeclaration",
    "ZeroCostDivision",
    "ZeroCostModeError",
    "ZeroCostModeReport",
    "ZeroCostRegistry",
    "ZeroCostViolationError",
    "enforce_zero_cost_mode",
    "load_default_registry",
    "read_workspace_dependencies",
    "scan_dependencies",
    "verify_zero_cost_mode",
]
