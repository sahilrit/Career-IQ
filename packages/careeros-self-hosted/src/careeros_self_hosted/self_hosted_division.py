"""SelfHostedDivision: the facade tying platform info, the data
directory bootstrap, and health checks together — the entry point a
CLI ``careeros doctor``-style command would call.
"""

from __future__ import annotations

from pathlib import Path

from careeros_self_hosted.bootstrap import DEFAULT_DATA_DIR, ensure_data_dir
from careeros_self_hosted.health_check import (
    HealthCheckResult,
    is_platform_ready,
    run_health_checks,
)
from careeros_self_hosted.platform_info import PlatformInfo, collect_platform_info


class SelfHostedDivision:
    def __init__(self, data_dir: Path | str = DEFAULT_DATA_DIR) -> None:
        self._data_dir = Path(data_dir)

    def platform_info(self) -> PlatformInfo:
        return collect_platform_info()

    def bootstrap(self) -> Path:
        return ensure_data_dir(self._data_dir)

    def run_health_checks(self) -> list[HealthCheckResult]:
        return run_health_checks(self._data_dir)

    def is_ready(self) -> bool:
        return is_platform_ready(self._data_dir)
