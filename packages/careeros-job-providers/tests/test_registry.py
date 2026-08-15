"""Tests for JobProviderRegistry."""

from __future__ import annotations

from careeros_job_providers import HealthStatus, JobProviderRegistry, JobSearchQuery


def test_search_all_aggregates_postings_from_every_healthy_provider(
    posting_factory, fake_provider_cls
):
    registry = JobProviderRegistry()
    registry.register(fake_provider_cls("remoteok", [posting_factory(source_provider="remoteok")]))
    registry.register(
        fake_provider_cls("wellfound", [posting_factory(source_provider="wellfound")])
    )

    result = registry.search_all(JobSearchQuery())

    assert len(result.postings) == 2


def test_search_all_excludes_down_providers(posting_factory, fake_provider_cls):
    registry = JobProviderRegistry()
    healthy = fake_provider_cls("remoteok", [posting_factory(source_provider="remoteok")])
    down = fake_provider_cls(
        "broken", [posting_factory(source_provider="broken")], health=HealthStatus.DOWN
    )
    registry.register(healthy)
    registry.register(down)

    result = registry.search_all(JobSearchQuery())

    assert len(result.postings) == 1
    assert down.search_calls == 0


def test_search_all_skips_a_provider_that_raises(posting_factory, fake_provider_cls):
    registry = JobProviderRegistry()
    broken = fake_provider_cls("broken", raise_on_search=True)
    healthy = fake_provider_cls("remoteok", [posting_factory(source_provider="remoteok")])
    registry.register(broken)
    registry.register(healthy)

    result = registry.search_all(JobSearchQuery())  # must not raise

    assert len(result.postings) == 1


def test_search_all_deduplicates_across_providers(posting_factory, fake_provider_cls):
    registry = JobProviderRegistry()
    registry.register(
        fake_provider_cls(
            "remoteok", [posting_factory(source_provider="remoteok", external_id="1")]
        )
    )
    registry.register(
        fake_provider_cls(
            "remoteok-mirror",
            [posting_factory(source_provider="remoteok", external_id="1")],
        )
    )

    result = registry.search_all(JobSearchQuery())

    assert len(result.postings) == 1


def test_search_all_applies_the_query_filter(posting_factory, fake_provider_cls):
    registry = JobProviderRegistry()
    registry.register(
        fake_provider_cls(
            "remoteok",
            [
                posting_factory(source_provider="remoteok", external_id="1", remote=True),
                posting_factory(source_provider="remoteok", external_id="2", remote=False),
            ],
        )
    )

    result = registry.search_all(JobSearchQuery(remote_only=True))

    assert len(result.postings) == 1
    assert result.postings[0].remote is True


def test_get_and_list_all_and_unregister(fake_provider_cls):
    registry = JobProviderRegistry()
    provider = fake_provider_cls("remoteok")
    registry.register(provider)

    assert registry.get("remoteok") is provider
    assert registry.list_all() == [provider]

    registry.unregister("remoteok")
    assert registry.get("remoteok") is None
    assert registry.list_all() == []
