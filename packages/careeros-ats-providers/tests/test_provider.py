"""AtsBoardProvider: error isolation, and the difference between an outage and
an empty result."""

from __future__ import annotations

import pytest

from careeros_ats_providers import AtsBoardProvider, BoardEntry, BoardFetchError
from careeros_ats_providers.adapter import AtsAdapter
from careeros_job_providers import HealthStatus, JobPosting, JobProviderError, JobSearchQuery


class StubAdapter(AtsAdapter):
    ats_id = "stub"
    allowed_hosts = frozenset({"example.com"})

    def __init__(self, *, per_board=None, failing=(), probe=None, bad_records=False):
        self._per_board = per_board or {}
        self._failing = set(failing)
        self._probe = probe
        self._bad_records = bad_records

    def fetch_board(self, entry, http):
        if entry.slug in self._failing:
            raise BoardFetchError(f"{entry.slug} is gone")
        count = self._per_board.get(entry.slug, 1)
        rows = [{"i": i, "slug": entry.slug} for i in range(count)]
        if self._bad_records:
            rows.append({"explode": True})
        return rows

    def to_posting(self, raw, entry):
        if raw.get("explode"):
            raise ValueError("unmappable record")
        return JobPosting(
            source_provider=self.ats_id,
            external_id=f"{entry.slug}-{raw['i']}",
            title=f"Role {raw['i']}",
            company_name=entry.name,
            url=f"https://example.com/{entry.slug}/{raw['i']}",
        )

    def probe_entry(self):
        return self._probe


BOARDS = [BoardEntry("alpha"), BoardEntry("beta"), BoardEntry("gamma")]
QUERY = JobSearchQuery(limit=100)


class TestSearch:
    def test_aggregates_every_board(self):
        provider = AtsBoardProvider(
            StubAdapter(per_board={"alpha": 2, "beta": 3, "gamma": 1}), BOARDS
        )
        assert len(provider.search(QUERY).postings) == 6

    def test_one_dead_board_does_not_sink_the_crawl(self):
        provider = AtsBoardProvider(StubAdapter(failing=["beta"]), BOARDS)
        result = provider.search(QUERY)
        assert len(result.postings) == 2
        # Skipped, but never silently: the reason is reported.
        assert any("beta is gone" in e for e in result.source_errors)

    def test_every_board_failing_is_an_outage_not_an_empty_result(self):
        # This is the distinction that matters upstream: returning [] here would
        # be indistinguishable from "this ATS had no matching jobs".
        provider = AtsBoardProvider(StubAdapter(failing=["alpha", "beta", "gamma"]), BOARDS)
        with pytest.raises(JobProviderError, match="every board failed"):
            provider.search(QUERY)

    def test_an_unmappable_record_is_skipped_not_fatal(self):
        provider = AtsBoardProvider(
            StubAdapter(per_board={"alpha": 1}, bad_records=True), [BOARDS[0]]
        )
        assert len(provider.search(QUERY).postings) == 1

    def test_no_boards_returns_empty_without_calling_the_adapter(self):
        assert AtsBoardProvider(StubAdapter(), []).search(QUERY).postings == []

    def test_respects_the_query_limit(self):
        provider = AtsBoardProvider(StubAdapter(per_board={"alpha": 50}), [BOARDS[0]])
        assert len(provider.search(JobSearchQuery(limit=5)).postings) == 5

    def test_provider_id_is_namespaced_by_ats(self):
        assert AtsBoardProvider(StubAdapter(), BOARDS).provider_id == "ats:stub"


class TestHealth:
    def test_healthy_when_the_probe_board_has_postings(self):
        adapter = StubAdapter(per_board={"probe": 3}, probe=BoardEntry("probe"))
        assert AtsBoardProvider(adapter, BOARDS).health_check().status is HealthStatus.HEALTHY

    def test_down_when_the_probe_board_fails(self):
        adapter = StubAdapter(failing=["probe"], probe=BoardEntry("probe"))
        health = AtsBoardProvider(adapter, BOARDS).health_check()
        assert health.status is HealthStatus.DOWN
        assert "probe" in health.detail

    def test_degraded_when_the_probe_answers_but_is_empty(self):
        # SmartRecruiters and Workable answer 200-with-nothing for a company
        # that does not exist, so reachability alone proves nothing.
        adapter = StubAdapter(per_board={"probe": 0}, probe=BoardEntry("probe"))
        health = AtsBoardProvider(adapter, BOARDS).health_check()
        assert health.status is HealthStatus.DEGRADED
        assert "no postings" in health.detail

    def test_no_probe_reports_healthy_rather_than_paying_for_a_crawl(self):
        assert AtsBoardProvider(StubAdapter(), BOARDS).health_check().status is HealthStatus.HEALTHY


class TestRegistryBuild:
    def test_only_ats_with_boards_are_built(self):
        from careeros_ats_providers import build_ats_providers

        providers = build_ats_providers()
        ids = {p.provider_id for p in providers}
        # Every built provider must actually have boards behind it; an empty
        # provider is noise in health output and can never return anything.
        assert all(p.boards for p in providers)
        assert "ats:greenhouse" in ids and "ats:workday" in ids

    def test_only_filter_narrows_the_set(self):
        from careeros_ats_providers import build_ats_providers

        providers = build_ats_providers(only=["greenhouse"])
        assert [p.provider_id for p in providers] == ["ats:greenhouse"]
