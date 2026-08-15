"""careeros_self_hosted: the Local / Self-Hosted Edition.

Real platform introspection (OS/Python/architecture), a health check
that a self-hosted install can actually run (writable data directory,
working SQLite store, browser automation and dashboard UI importable),
and the canonical local data-directory bootstrap every entry point
shares.
"""

from careeros_self_hosted.bootstrap import DEFAULT_DATA_DIR, ensure_data_dir
from careeros_self_hosted.exceptions import SelfHostedError
from careeros_self_hosted.health_check import (
    HealthCheckResult,
    is_platform_ready,
    run_health_checks,
)
from careeros_self_hosted.platform_info import (
    PlatformInfo,
    collect_platform_info,
    is_os_supported,
)
from careeros_self_hosted.self_hosted_division import SelfHostedDivision

__all__ = [
    "DEFAULT_DATA_DIR",
    "HealthCheckResult",
    "PlatformInfo",
    "SelfHostedDivision",
    "SelfHostedError",
    "collect_platform_info",
    "ensure_data_dir",
    "is_os_supported",
    "is_platform_ready",
    "run_health_checks",
]
