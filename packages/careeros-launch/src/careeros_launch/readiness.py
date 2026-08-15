"""Launch readiness: pure aggregation over caller-supplied checks, so
it's testable against fixtures — the real run wires in
``importlib.util.find_spec`` for property presence and Phase 46's own
workspace dependency audit for the zero-cost-API claim.
"""

from __future__ import annotations

import importlib.util
from collections.abc import Callable

from pydantic import BaseModel


class PropertyReadiness(BaseModel):
    property_name: str
    package_name: str
    is_satisfied: bool


class LaunchReadinessReport(BaseModel):
    properties: list[PropertyReadiness]
    zero_cost_violations: dict[str, list[str]]

    @property
    def is_ready(self) -> bool:
        all_properties_satisfied = all(prop.is_satisfied for prop in self.properties)
        return all_properties_satisfied and not self.zero_cost_violations

    @property
    def unsatisfied_properties(self) -> list[PropertyReadiness]:
        return [prop for prop in self.properties if not prop.is_satisfied]


def _default_import_checker(package_name: str) -> bool:
    return importlib.util.find_spec(package_name) is not None


def verify_launch_readiness(
    required_properties: list[tuple[str, str]],
    *,
    zero_cost_violations: dict[str, list[str]],
    import_checker: Callable[[str], bool] = _default_import_checker,
) -> LaunchReadinessReport:
    properties = [
        PropertyReadiness(
            property_name=property_name,
            package_name=package_name,
            is_satisfied=import_checker(package_name),
        )
        for property_name, package_name in required_properties
    ]
    return LaunchReadinessReport(properties=properties, zero_cost_violations=zero_cost_violations)
