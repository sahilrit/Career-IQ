"""careeros_launch: Production Launch.

A real readiness gate over the platform's architectural properties
(multi-tenant, plugin-based, event-driven, autonomous, memory-driven,
AI-powered, browser-capable, SaaS-ready — each backed by an actual
shipped package) plus the zero-paid-API-dependent claim, checked
functionally against the live workspace via Phase 46's own dependency
audit rather than by import presence. A launch is only ever recorded
once the gate passes.
"""

from careeros_launch.exceptions import LaunchError, LaunchNotReadyError
from careeros_launch.launch_division import LaunchDivision
from careeros_launch.launch_record import LaunchRecord, LaunchRecordRepository
from careeros_launch.properties import DEFAULT_LAUNCH_PROPERTIES
from careeros_launch.readiness import (
    LaunchReadinessReport,
    PropertyReadiness,
    verify_launch_readiness,
)

__all__ = [
    "DEFAULT_LAUNCH_PROPERTIES",
    "LaunchDivision",
    "LaunchError",
    "LaunchNotReadyError",
    "LaunchReadinessReport",
    "LaunchRecord",
    "LaunchRecordRepository",
    "PropertyReadiness",
    "verify_launch_readiness",
]
