"""CapabilityMarketplace: ranking, fallback, parallel execution, and
versioning on top of Phase 23's capability registry pattern — the
answer to "which capability do I need?" instead of "which plugin should
I call?".
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any

from careeros_capability_marketplace.exceptions import NoProviderAvailableError
from careeros_common import get_logger
from careeros_plugin_sdk import satisfies

logger = get_logger(__name__)


@dataclass
class ProviderRecord:
    provider_id: str
    provider: Any
    version: str = "1.0.0"
    priority: int = 0
    health_check: Callable[[], bool] | None = None

    def is_healthy(self) -> bool:
        if self.health_check is None:
            return True
        try:
            return bool(self.health_check())
        except Exception:
            logger.exception("Health check raised for provider %s", self.provider_id)
            return False


class CapabilityMarketplace:
    def __init__(self) -> None:
        self._providers: dict[str, dict[str, ProviderRecord]] = {}

    def register(self, capability: str, record: ProviderRecord) -> None:
        self._providers.setdefault(capability, {})[record.provider_id] = record

    def unregister(self, capability: str, provider_id: str) -> None:
        self._providers.get(capability, {}).pop(provider_id, None)

    def discover(
        self, capability: str, *, version_constraint: str | None = None
    ) -> list[ProviderRecord]:
        records = list(self._providers.get(capability, {}).values())
        if version_constraint is not None:
            records = [r for r in records if satisfies(r.version, version_constraint)]
        return records

    def ranked(
        self, capability: str, *, version_constraint: str | None = None
    ) -> list[ProviderRecord]:
        """Healthy providers only, highest priority first."""
        records = self.discover(capability, version_constraint=version_constraint)
        healthy = [record for record in records if record.is_healthy()]
        return sorted(healthy, key=lambda record: record.priority, reverse=True)

    def call_with_fallback[T](
        self,
        capability: str,
        invoke: Callable[[Any], T],
        *,
        version_constraint: str | None = None,
    ) -> T:
        """Try each ranked provider in priority order; return the first success."""
        candidates = self.ranked(capability, version_constraint=version_constraint)
        if not candidates:
            raise NoProviderAvailableError(
                f"No healthy provider available for capability {capability!r}"
            )

        last_error: Exception | None = None
        for record in candidates:
            try:
                return invoke(record.provider)
            except Exception as exc:
                last_error = exc
                logger.warning("Provider %s failed for %s: %s", record.provider_id, capability, exc)
        assert last_error is not None
        raise last_error

    def call_all_parallel[T](
        self,
        capability: str,
        invoke: Callable[[Any], T],
        *,
        version_constraint: str | None = None,
    ) -> list[T]:
        """Call every ranked provider concurrently; skip ones that raise."""
        candidates = self.ranked(capability, version_constraint=version_constraint)
        if not candidates:
            return []

        results: list[T] = []
        with ThreadPoolExecutor(max_workers=len(candidates)) as executor:
            future_to_record = {
                executor.submit(invoke, record.provider): record for record in candidates
            }
            for future in as_completed(future_to_record):
                record = future_to_record[future]
                try:
                    results.append(future.result())
                except Exception:
                    logger.exception("Provider %s failed for %s", record.provider_id, capability)
        return results
