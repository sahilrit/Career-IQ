"""AtsBoardProvider: one JobProvider per ATS, driving one adapter over many
company boards.

The crawl loop, error isolation, concurrency and health check are written once
here rather than once per ATS. A board that 404s (companies change board
tokens constantly) is skipped and *counted*, never fatal — but if EVERY board
fails, that is a real outage and the provider says so instead of quietly
returning nothing, which would look identical to "no matching jobs" upstream.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from careeros_ats_providers.adapter import AtsAdapter, BoardEntry
from careeros_ats_providers.http import AtsHttp, BoardFetchError
from careeros_common import get_logger
from careeros_job_providers import (
    HealthStatus,
    JobPosting,
    JobProvider,
    JobProviderError,
    JobSearchQuery,
    JobSearchResult,
    ProviderHealth,
    filter_postings,
)

logger = get_logger(__name__)

DEFAULT_MAX_WORKERS = 8


class AtsBoardProvider(JobProvider):
    def __init__(
        self,
        adapter: AtsAdapter,
        boards: list[BoardEntry],
        *,
        http: AtsHttp | None = None,
        max_workers: int = DEFAULT_MAX_WORKERS,
    ) -> None:
        self._adapter = adapter
        self._boards = list(boards)
        self._http = http or AtsHttp()
        self._max_workers = max_workers

    @property
    def provider_id(self) -> str:
        return f"ats:{self._adapter.ats_id}"

    @property
    def boards(self) -> list[BoardEntry]:
        return list(self._boards)

    def _crawl_board(self, entry: BoardEntry) -> tuple[list[JobPosting], str | None]:
        try:
            raw_jobs = self._adapter.fetch_board(entry, self._http)
        except BoardFetchError as exc:
            return [], f"{entry.slug}: {exc}"
        except Exception as exc:
            logger.exception("ATS %s board %s raised", self._adapter.ats_id, entry.slug)
            return [], f"{entry.slug}: unexpected failure: {exc}"

        postings: list[JobPosting] = []
        for raw in raw_jobs:
            try:
                posting = self._adapter.to_posting(raw, entry)
            except Exception as exc:
                logger.warning(
                    "ATS %s: could not normalize a posting from %s: %s",
                    self._adapter.ats_id,
                    entry.slug,
                    exc,
                )
                continue
            if posting is not None and posting.title:
                postings.append(posting)
        return postings, None

    def search(self, query: JobSearchQuery) -> JobSearchResult:
        if not self._boards:
            return JobSearchResult(postings=[])

        all_postings: list[JobPosting] = []
        errors: list[str] = []
        workers = min(self._max_workers, len(self._boards))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for postings, error in pool.map(self._crawl_board, self._boards):
                all_postings.extend(postings)
                if error:
                    errors.append(error)

        if errors and len(errors) == len(self._boards):
            # Total failure is an outage, not an empty result set. Raising lets
            # the registry record it in source_errors instead of it looking
            # like this ATS simply had no matching jobs.
            raise JobProviderError(
                f"{self._adapter.ats_id}: every board failed — {errors[0]}"
                + (f" (and {len(errors) - 1} more)" if len(errors) > 1 else "")
            )

        filtered = filter_postings(all_postings, query)
        return JobSearchResult(
            postings=filtered[: query.limit],
            source_errors=[f"{self.provider_id}: {e}" for e in errors],
        )

    def health_check(self) -> ProviderHealth:
        """Fetch one known-live board, not the whole set.

        A full crawl would double the cost of every search just to answer a
        question the search itself is about to answer. An adapter with no probe
        board reports healthy and lets the real search surface any problem.
        """
        probe = self._adapter.probe_entry()
        if probe is None or not self._boards:
            return ProviderHealth(status=HealthStatus.HEALTHY)
        try:
            jobs = self._adapter.probe_board(probe, self._http)
        except Exception as exc:
            return ProviderHealth(
                status=HealthStatus.DOWN,
                detail=f"probe board {probe.slug!r} unreachable: {exc}",
            )
        if not jobs:
            # SmartRecruiters and Workable answer 200 with an EMPTY board for a
            # company that does not exist, so reachability alone proves nothing.
            # A probe board is chosen because it reliably has open roles; zero
            # from it means the response shape changed or the board moved.
            return ProviderHealth(
                status=HealthStatus.DEGRADED,
                detail=(
                    f"probe board {probe.slug!r} answered but returned no postings — "
                    "the API shape may have changed"
                ),
            )
        return ProviderHealth(status=HealthStatus.HEALTHY)

    def close(self) -> None:
        self._http.close()
