"""Platform health check: real checks that a self-hosted install can
actually run — a writable data directory, a working SQLite store, and
the two heaviest optional-but-commonly-needed dependencies (browser
automation, the dashboard UI) actually importable. Each check reports
pass/fail with a detail message rather than raising, so one broken
piece doesn't hide the status of the rest.
"""

from __future__ import annotations

import importlib.util
import uuid
from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel

from careeros_common import DocumentStore


class HealthCheckResult(BaseModel):
    check_name: str
    passed: bool
    detail: str = ""


def _check_data_dir_writable(data_dir: Path) -> HealthCheckResult:
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        probe_path = data_dir / f".health_check_{uuid.uuid4().hex}"
        probe_path.write_text("ok")
        probe_path.unlink()
    except OSError as error:
        return HealthCheckResult(check_name="data_dir_writable", passed=False, detail=str(error))
    return HealthCheckResult(check_name="data_dir_writable", passed=True)


def _check_sqlite_store(data_dir: Path) -> HealthCheckResult:
    try:
        store = DocumentStore(data_dir / "health_check.db")
        store.put("health_check", "probe", {"ok": True})
        result = store.get("health_check", "probe")
        store.delete("health_check", "probe")
        store.close()
    except Exception as error:
        return HealthCheckResult(check_name="sqlite_store", passed=False, detail=str(error))
    return HealthCheckResult(check_name="sqlite_store", passed=result.get("ok") is True)


def _check_module_importable(module_name: str, check_name: str) -> HealthCheckResult:
    is_available = importlib.util.find_spec(module_name) is not None
    detail = "" if is_available else f"{module_name!r} is not installed"
    return HealthCheckResult(check_name=check_name, passed=is_available, detail=detail)


def _check_browser_automation() -> HealthCheckResult:
    return _check_module_importable("playwright", "browser_automation")


def _check_dashboard_ui() -> HealthCheckResult:
    return _check_module_importable("streamlit", "dashboard_ui")


def run_health_checks(data_dir: Path | str) -> list[HealthCheckResult]:
    resolved = Path(data_dir)
    checks: list[Callable[[], HealthCheckResult]] = [
        lambda: _check_data_dir_writable(resolved),
        lambda: _check_sqlite_store(resolved),
        _check_browser_automation,
        _check_dashboard_ui,
    ]
    return [check() for check in checks]


def is_platform_ready(data_dir: Path | str) -> bool:
    return all(result.passed for result in run_health_checks(data_dir))
