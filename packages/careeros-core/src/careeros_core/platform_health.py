"""PlatformHealthMonitor: one aggregated health report across every
subsystem CareerOS Core knows about, instead of each caller polling N
different health-check methods separately.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class ComponentStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


@dataclass
class ComponentHealth:
    name: str
    status: ComponentStatus
    detail: str = ""


@dataclass
class PlatformHealthReport:
    components: list[ComponentHealth] = field(default_factory=list)
    checked_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def overall_status(self) -> ComponentStatus:
        statuses = {component.status for component in self.components}
        if ComponentStatus.DOWN in statuses:
            return ComponentStatus.DOWN
        if ComponentStatus.DEGRADED in statuses:
            return ComponentStatus.DEGRADED
        return ComponentStatus.HEALTHY


HealthCheck = Callable[[], ComponentHealth]


class PlatformHealthMonitor:
    def __init__(self) -> None:
        self._checks: dict[str, HealthCheck] = {}

    def register_check(self, name: str, check: HealthCheck) -> None:
        self._checks[name] = check

    def run(self) -> PlatformHealthReport:
        components = []
        for name, check in self._checks.items():
            try:
                components.append(check())
            except Exception as exc:
                components.append(
                    ComponentHealth(name=name, status=ComponentStatus.DOWN, detail=str(exc))
                )
        return PlatformHealthReport(components=components)
