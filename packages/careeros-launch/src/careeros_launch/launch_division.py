"""LaunchDivision: the facade tying the readiness gate (backed by Phase
46's real workspace dependency audit) and the launch record together —
``announce_launch`` refuses to record a launch unless the gate passes,
so a recorded launch is a real claim, not a hopeful one.
"""

from __future__ import annotations

from pathlib import Path

from careeros_common import DocumentStore
from careeros_launch.exceptions import LaunchNotReadyError
from careeros_launch.launch_record import LaunchRecord, LaunchRecordRepository
from careeros_launch.properties import DEFAULT_LAUNCH_PROPERTIES
from careeros_launch.readiness import LaunchReadinessReport, verify_launch_readiness
from careeros_zero_cost_mode import ZeroCostDivision


class LaunchDivision:
    def __init__(self, store: DocumentStore) -> None:
        self._records = LaunchRecordRepository(store)
        self._zero_cost = ZeroCostDivision()

    def check_readiness(self, *, packages_dir: str | Path) -> LaunchReadinessReport:
        violations = self._zero_cost.audit_workspace_dependencies(packages_dir)
        return verify_launch_readiness(DEFAULT_LAUNCH_PROPERTIES, zero_cost_violations=violations)

    def announce_launch(
        self, *, version: str, notes: str = "", packages_dir: str | Path
    ) -> LaunchRecord:
        report = self.check_readiness(packages_dir=packages_dir)
        if not report.is_ready:
            raise LaunchNotReadyError(
                f"Launch readiness gate failed: "
                f"unsatisfied={[p.property_name for p in report.unsatisfied_properties]}, "
                f"zero_cost_violations={report.zero_cost_violations}"
            )
        record = LaunchRecord(version=version, notes=notes)
        self._records.save(record)
        return record

    def latest_launch(self) -> LaunchRecord | None:
        return self._records.latest()
