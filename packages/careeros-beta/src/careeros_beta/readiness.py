"""Beta readiness: checks the MVP's required subsystems are actually
installed in this workspace — ``verify_beta_readiness`` is a pure
function over a caller-supplied import checker (so it's testable
against fixtures), and ``importlib.util.find_spec`` is the real checker
used for an actual run against this repo.
"""

from __future__ import annotations

import importlib.util
from collections.abc import Callable

from pydantic import BaseModel


class ComponentReadiness(BaseModel):
    component_name: str
    package_name: str
    is_importable: bool


class BetaReadinessReport(BaseModel):
    statuses: list[ComponentReadiness]

    @property
    def is_ready(self) -> bool:
        return all(status.is_importable for status in self.statuses)

    @property
    def missing(self) -> list[ComponentReadiness]:
        return [status for status in self.statuses if not status.is_importable]


def _default_import_checker(package_name: str) -> bool:
    return importlib.util.find_spec(package_name) is not None


def verify_beta_readiness(
    required_components: list[tuple[str, str]],
    *,
    import_checker: Callable[[str], bool] = _default_import_checker,
) -> BetaReadinessReport:
    statuses = [
        ComponentReadiness(
            component_name=component_name,
            package_name=package_name,
            is_importable=import_checker(package_name),
        )
        for component_name, package_name in required_components
    ]
    return BetaReadinessReport(statuses=statuses)
