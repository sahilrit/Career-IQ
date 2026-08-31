"""Tests for JobProviderRegistry."""

from __future__ import annotations

import time

from careeros_job_providers import HealthStatus, JobProviderRegistry, JobSearchQuery


def test_search_all_aggregates_postings_from_every_healthy_provider(
    posting_factory, fake_provider_cls
):
    registry = JobProviderRegistry()
    # Two genuinely DIFFERENT jobs: the factory's defaults would otherwise
    # produce the same company/title/url twice, which cross-provider dedupe
    # correctly collapses into one.
    registry.register(
        fake_provider_cls(
            "remoteok",
            [posting_factory(source_provider="remoteok", url="https://remoteok.com/jobs/1")],
        )
    )
    registry.register(
        fake_provider_cls(
            "wellfound",
            [
                posting_factory(
                    source_provider="wellfound",
                    title="Product Designer",
                    url="https://wellfound.com/jobs/9",
                )
            ],
        )
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


# --- failure reporting -------------------------------------------------------
# A provider that breaks used to vanish silently: search_all swallowed the
# exception into an empty list, so the user saw fewer results and no reason.


def test_search_all_reports_a_failing_provider(posting_factory, fake_provider_cls):
    registry = JobProviderRegistry()
    registry.register(fake_provider_cls("good", [posting_factory(source_provider="good")]))
    registry.register(fake_provider_cls("broken", search_error=RuntimeError("429 rate limited")))

    result = registry.search_all(JobSearchQuery())

    assert len(result.postings) == 1
    assert len(result.source_errors) == 1
    assert "broken" in result.source_errors[0]
    assert "429 rate limited" in result.source_errors[0]


def test_search_all_reports_a_down_provider_rather_than_hiding_it(
    posting_factory, fake_provider_cls
):
    registry = JobProviderRegistry()
    registry.register(fake_provider_cls("good", [posting_factory(source_provider="good")]))
    registry.register(fake_provider_cls("offline", health=HealthStatus.DOWN))

    result = registry.search_all(JobSearchQuery())

    assert any("offline" in error for error in result.source_errors)


def test_search_all_reports_nothing_when_every_provider_works(posting_factory, fake_provider_cls):
    registry = JobProviderRegistry()
    registry.register(fake_provider_cls("good", [posting_factory(source_provider="good")]))
    assert registry.search_all(JobSearchQuery()).source_errors == []


# --- timeouts ----------------------------------------------------------------
# One hung provider must not hold the whole search open. We cannot kill the
# worker thread, but we can stop waiting on it and return what we have.


def test_a_slow_provider_does_not_block_the_others(posting_factory, fake_provider_cls):
    registry = JobProviderRegistry(search_timeout_seconds=0.05)
    registry.register(fake_provider_cls("fast", [posting_factory(source_provider="fast")]))
    registry.register(
        fake_provider_cls("slow", [posting_factory(source_provider="slow")], search_delay_seconds=5)
    )

    result = registry.search_all(JobSearchQuery())

    assert {p.source_provider for p in result.postings} == {"fast"}
    assert any("slow" in error and "timed out" in error for error in result.source_errors)


def test_a_slow_health_check_does_not_block_the_search(posting_factory, fake_provider_cls):
    registry = JobProviderRegistry(health_timeout_seconds=0.05)
    registry.register(fake_provider_cls("fast", [posting_factory(source_provider="fast")]))
    registry.register(
        fake_provider_cls(
            "sluggish",
            [posting_factory(source_provider="sluggish")],
            health_delay_seconds=5,
        )
    )

    result = registry.search_all(JobSearchQuery())

    assert {p.source_provider for p in result.postings} == {"fast"}
    assert any("sluggish" in error for error in result.source_errors)


def test_the_timeouts_have_usable_defaults():
    registry = JobProviderRegistry()
    assert registry.search_timeout_seconds > 0
    assert registry.health_timeout_seconds > 0


def test_an_empty_registry_returns_an_empty_result():
    result = JobProviderRegistry().search_all(JobSearchQuery())
    assert result.postings == []
    assert result.source_errors == []


def test_the_search_timeout_actually_bounds_wall_clock(posting_factory, fake_provider_cls):
    """Timing out the result collection is not enough on its own: exiting a
    ThreadPoolExecutor context manager joins every worker, which would put the
    slow provider's full duration back into the caller's wall-clock."""
    registry = JobProviderRegistry(search_timeout_seconds=0.05)
    registry.register(fake_provider_cls("fast", [posting_factory(source_provider="fast")]))
    registry.register(fake_provider_cls("slow", search_delay_seconds=10))

    started = time.monotonic()
    registry.search_all(JobSearchQuery())
    elapsed = time.monotonic() - started

    assert elapsed < 2.0, f"search_all waited {elapsed:.1f}s for a provider it had given up on"


def test_the_health_timeout_actually_bounds_wall_clock(posting_factory, fake_provider_cls):
    registry = JobProviderRegistry(health_timeout_seconds=0.05)
    registry.register(fake_provider_cls("fast", [posting_factory(source_provider="fast")]))
    registry.register(fake_provider_cls("sluggish", health_delay_seconds=10))

    started = time.monotonic()
    registry.search_all(JobSearchQuery())
    elapsed = time.monotonic() - started

    assert elapsed < 2.0, f"search_all waited {elapsed:.1f}s on a health check it abandoned"
