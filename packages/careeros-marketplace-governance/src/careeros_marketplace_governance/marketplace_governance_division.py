"""MarketplaceGovernanceDivision: the facade tying review policy and
version history/rollback together.
"""

from __future__ import annotations

from collections.abc import Callable

from careeros_common import DocumentStore
from careeros_marketplace_governance.governance_review import (
    GovernanceReport,
    run_governance_review,
)
from careeros_marketplace_governance.version_rollback import (
    PluginVersionRecord,
    PluginVersionRepository,
    current_version,
    publish_version,
    rollback_to,
)
from careeros_plugin_sdk import PluginManifest


class MarketplaceGovernanceDivision:
    def __init__(
        self,
        store: DocumentStore,
        *,
        allowed_permissions: frozenset[str] = frozenset(),
        dangerous_permissions: frozenset[str] = frozenset(),
    ) -> None:
        self._versions = PluginVersionRepository(store)
        self._allowed_permissions = allowed_permissions
        self._dangerous_permissions = dangerous_permissions

    def review(
        self,
        manifest: PluginManifest,
        *,
        known_plugin_ids: frozenset[str] = frozenset(),
        build_fn: Callable[[], object] | None = None,
    ) -> GovernanceReport:
        return run_governance_review(
            manifest,
            allowed_permissions=self._allowed_permissions,
            dangerous_permissions=self._dangerous_permissions,
            known_plugin_ids=known_plugin_ids,
            build_fn=build_fn,
        )

    def publish_version(self, plugin_id: str, version: str) -> PluginVersionRecord:
        return publish_version(self._versions, plugin_id, version)

    def current_version(self, plugin_id: str) -> str | None:
        return current_version(self._versions, plugin_id)

    def rollback_to(self, plugin_id: str, version: str) -> PluginVersionRecord:
        return rollback_to(self._versions, plugin_id, version)

    def version_history(self, plugin_id: str) -> list[PluginVersionRecord]:
        return self._versions.list_for_plugin(plugin_id)
