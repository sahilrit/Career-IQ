"""Registry of job providers implementing the FIND_JOBS capability.

The rest of CareerOS asks the registry for "every healthy FIND_JOBS
provider" and aggregates results — it never imports a specific provider
like RemoteOK directly. Phase 24 (Capability Marketplace) generalizes
this pattern to every capability; this is its first working instance.

Two properties matter more than they used to, now that some providers
read live sites rather than steady public feeds:

* **A failing source is reported, never hidden.** A provider that raises
  or is down contributes an entry to ``source_errors`` instead of
  silently reducing the result count.
* **A hung source cannot hold the search open.** Every provider call is
  bounded by a timeout.
"""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError

from careeros_common import get_logger
from careeros_job_providers.dedupe import deduplicate
from careeros_job_providers.filtering import filter_postings
from careeros_job_providers.models import JobPosting, JobSearchQuery
from careeros_job_providers.provider import HealthStatus, JobProvider, JobSearchResult

logger = get_logger(__name__)

#: A provider that has not answered in this long is treated as unavailable for
#: this run. Generous enough for a paged site crawl, short enough that a user
#: is not left staring at a spinner.
DEFAULT_SEARCH_TIMEOUT_SECONDS = 120.0

#: Health checks run before every search, so they get a much tighter bound.
DEFAULT_HEALTH_TIMEOUT_SECONDS = 15.0


def _release(pool: ThreadPoolExecutor) -> None:
    """Stop waiting on a pool without joining its workers.

    ``ThreadPoolExecutor`` as a context manager calls ``shutdown(wait=True)``
    on exit, which joins every thread — so a provider we already timed out on
    would put its full duration straight back into the caller's wall-clock.
    Releasing without waiting is the whole point of having a timeout. Queued
    work is cancelled; a thread already running finishes into a result nobody
    reads, and the interpreter joins it at exit.
    """
    pool.shutdown(wait=False, cancel_futures=True)


class JobProviderRegistry:
    def __init__(
        self,
        *,
        search_timeout_seconds: float = DEFAULT_SEARCH_TIMEOUT_SECONDS,
        health_timeout_seconds: float = DEFAULT_HEALTH_TIMEOUT_SECONDS,
    ) -> None:
        self._providers: dict[str, JobProvider] = {}
        self.search_timeout_seconds = search_timeout_seconds
        self.health_timeout_seconds = health_timeout_seconds

    def register(self, provider: JobProvider) -> None:
        self._providers[provider.provider_id] = provider

    def unregister(self, provider_id: str) -> None:
        self._providers.pop(provider_id, None)

    def get(self, provider_id: str) -> JobProvider | None:
        return self._providers.get(provider_id)

    def list_all(self) -> list[JobProvider]:
        return list(self._providers.values())

    # -- internals ----------------------------------------------------------

    @staticmethod
    def _await(
        future: Future,
        *,
        timeout: float,
        provider_id: str,
        action: str,
        errors: list[str],
    ):
        """Wait for one provider call, recording why it produced nothing.

        A timeout does not kill the worker thread — Python has no safe way to
        do that — it stops *us* waiting. The thread finishes into a result
        nobody reads, and the pool releases it on shutdown.
        """
        try:
            return future.result(timeout=timeout)
        except FutureTimeoutError:
            future.cancel()
            errors.append(f"{provider_id}: {action} timed out after {timeout:g}s")
            logger.warning("Provider %s %s timed out", provider_id, action)
        except Exception as exc:
            errors.append(f"{provider_id}: {action} failed — {exc}")
            logger.exception("Provider %s %s failed", provider_id, action)
        return None

    def healthy_providers(self, errors: list[str] | None = None) -> list[JobProvider]:
        """Every registered provider whose health check does not report DOWN.

        Providers are health-checked concurrently — several of them crawl many
        company boards, so serial checks would dominate wall-clock.
        """
        providers = self.list_all()
        if not providers:
            return []

        collected: list[str] = errors if errors is not None else []
        live: list[JobProvider] = []

        pool = ThreadPoolExecutor(max_workers=len(providers))
        try:
            futures = {
                provider.provider_id: pool.submit(provider.health_check) for provider in providers
            }
            for provider in providers:
                health = self._await(
                    futures[provider.provider_id],
                    timeout=self.health_timeout_seconds,
                    provider_id=provider.provider_id,
                    action="health check",
                    errors=collected,
                )
                if health is None:
                    continue
                if health.status is HealthStatus.DOWN:
                    detail = f" — {health.detail}" if health.detail else ""
                    collected.append(f"{provider.provider_id}: unavailable{detail}")
                    continue
                live.append(provider)
        finally:
            _release(pool)

        return live

    def search_all(self, query: JobSearchQuery) -> JobSearchResult:
        """Query every healthy provider concurrently, then filter, dedupe and
        aggregate. A single provider's failure is recorded in ``source_errors``
        and skipped rather than failing the whole aggregate search.
        """
        source_errors: list[str] = []
        providers = self.healthy_providers(source_errors)
        all_postings: list[JobPosting] = []

        if providers:
            pool = ThreadPoolExecutor(max_workers=len(providers))
            try:
                futures = {
                    provider.provider_id: pool.submit(provider.search, query)
                    for provider in providers
                }
                for provider in providers:
                    result = self._await(
                        futures[provider.provider_id],
                        timeout=self.search_timeout_seconds,
                        provider_id=provider.provider_id,
                        action="search",
                        errors=source_errors,
                    )
                    if result is not None:
                        all_postings.extend(result.postings)
            finally:
                _release(pool)

        filtered = filter_postings(all_postings, query)
        deduped = deduplicate(filtered)
        return JobSearchResult(postings=deduped, source_errors=source_errors)
