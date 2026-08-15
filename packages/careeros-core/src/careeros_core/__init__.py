"""careeros_core: the platform kernel. Deliberately thin — it does not
re-export domain packages (Career Brain, Memory, providers, ...), which
already have clean independent boundaries. It only holds what Phase 23
newly introduces: a generic capability registry, aggregated platform
health, a shared execution context, and optional event contracts.
"""

from careeros_core.capability_registry import CapabilityRegistry
from careeros_core.event_contracts import EventContractRegistry
from careeros_core.exceptions import ContractViolationError, CoreError
from careeros_core.execution_context import ExecutionContext
from careeros_core.platform_health import (
    ComponentHealth,
    ComponentStatus,
    PlatformHealthMonitor,
    PlatformHealthReport,
)

__all__ = [
    "CapabilityRegistry",
    "ComponentHealth",
    "ComponentStatus",
    "ContractViolationError",
    "CoreError",
    "EventContractRegistry",
    "ExecutionContext",
    "PlatformHealthMonitor",
    "PlatformHealthReport",
]
