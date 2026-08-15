"""The platform's own real architectural properties — each entry names
an actual package that makes the claim true, not a generic checklist.
Zero-paid-API dependence is deliberately not listed here: it's checked
functionally against the live workspace via Phase 46's dependency
audit, not by import presence.
"""

from __future__ import annotations

DEFAULT_LAUNCH_PROPERTIES: list[tuple[str, str]] = [
    ("multi_tenant", "careeros_tenancy"),
    ("plugin_based", "careeros_plugin_sdk"),
    ("event_driven", "careeros_event_bus"),
    ("autonomous", "careeros_autonomy"),
    ("memory_driven", "careeros_memory"),
    ("ai_powered", "careeros_career_intelligence"),
    ("browser_capable", "careeros_browser"),
    ("saas_ready", "careeros_billing"),
]
