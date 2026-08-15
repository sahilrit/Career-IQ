"""Zero-Cost Mode report: checks every required capability against the
registry and reports which ones have no free path, rather than
crashing on the first violation — useful for a real audit run that
wants the full picture, not just the first failure.
"""

from __future__ import annotations

from pydantic import BaseModel

from careeros_zero_cost_mode.exceptions import ZeroCostViolationError
from careeros_zero_cost_mode.registry import ZeroCostRegistry


class CapabilityCostStatus(BaseModel):
    capability_name: str
    has_free_path: bool
    provider_count: int


class ZeroCostModeReport(BaseModel):
    statuses: list[CapabilityCostStatus]

    @property
    def is_fully_zero_cost(self) -> bool:
        return all(status.has_free_path for status in self.statuses)

    @property
    def violations(self) -> list[CapabilityCostStatus]:
        return [status for status in self.statuses if not status.has_free_path]


def verify_zero_cost_mode(
    registry: ZeroCostRegistry, required_capabilities: list[str]
) -> ZeroCostModeReport:
    statuses = [
        CapabilityCostStatus(
            capability_name=capability,
            has_free_path=registry.has_free_path(capability),
            provider_count=len(registry.providers_for_capability(capability)),
        )
        for capability in required_capabilities
    ]
    return ZeroCostModeReport(statuses=statuses)


def enforce_zero_cost_mode(registry: ZeroCostRegistry, required_capabilities: list[str]) -> None:
    """Raises if any required capability has no free path — for a hard gate."""
    report = verify_zero_cost_mode(registry, required_capabilities)
    if not report.is_fully_zero_cost:
        names = ", ".join(status.capability_name for status in report.violations)
        raise ZeroCostViolationError(f"No free provider path for: {names}")
