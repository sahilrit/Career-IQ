"""Platform performance: the same funnel metrics, broken down by
Application.source_provider — the real field every job/gig provider
(Phase 6-8, 18-19) already stamps onto every posting.
"""

from __future__ import annotations

from careeros_analytics.application_funnel import (
    ApplicationFunnelMetrics,
    compute_application_funnel,
)
from careeros_career_brain import Application

_UNKNOWN_PLATFORM = "unknown"


def compute_platform_performance(
    applications: list[Application],
) -> dict[str, ApplicationFunnelMetrics]:
    grouped: dict[str, list[Application]] = {}
    for application in applications:
        key = application.source_provider or _UNKNOWN_PLATFORM
        grouped.setdefault(key, []).append(application)
    return {platform: compute_application_funnel(apps) for platform, apps in grouped.items()}
