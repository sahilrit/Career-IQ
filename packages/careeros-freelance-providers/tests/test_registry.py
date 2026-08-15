"""Tests for FreelanceProviderRegistry."""

from __future__ import annotations

from careeros_freelance_providers import FreelanceProviderRegistry, GigSearchQuery, HealthStatus


def test_search_all_aggregates_postings_from_every_healthy_provider(
    posting_factory, fake_provider_cls
):
    registry = FreelanceProviderRegistry()
    registry.register(fake_provider_cls("fiverr", [posting_factory(source_provider="fiverr")]))
    registry.register(fake_provider_cls("upwork", [posting_factory(source_provider="upwork")]))

    result = registry.search_all(GigSearchQuery())

    assert len(result.postings) == 2


def test_search_all_excludes_down_providers(posting_factory, fake_provider_cls):
    registry = FreelanceProviderRegistry()
    healthy = fake_provider_cls("fiverr", [posting_factory(source_provider="fiverr")])
    down = fake_provider_cls(
        "broken", [posting_factory(source_provider="broken")], health=HealthStatus.DOWN
    )
    registry.register(healthy)
    registry.register(down)

    result = registry.search_all(GigSearchQuery())

    assert len(result.postings) == 1
    assert down.search_calls == 0


def test_search_all_skips_a_provider_that_raises(posting_factory, fake_provider_cls):
    registry = FreelanceProviderRegistry()
    broken = fake_provider_cls("broken", raise_on_search=True)
    healthy = fake_provider_cls("fiverr", [posting_factory(source_provider="fiverr")])
    registry.register(broken)
    registry.register(healthy)

    result = registry.search_all(GigSearchQuery())  # must not raise

    assert len(result.postings) == 1


def test_search_all_deduplicates_across_providers(posting_factory, fake_provider_cls):
    registry = FreelanceProviderRegistry()
    registry.register(
        fake_provider_cls("fiverr", [posting_factory(source_provider="fiverr", external_id="1")])
    )
    registry.register(
        fake_provider_cls(
            "fiverr-mirror", [posting_factory(source_provider="fiverr", external_id="1")]
        )
    )

    result = registry.search_all(GigSearchQuery())

    assert len(result.postings) == 1


def test_get_and_list_all_and_unregister(fake_provider_cls):
    registry = FreelanceProviderRegistry()
    provider = fake_provider_cls("fiverr")
    registry.register(provider)

    assert registry.get("fiverr") is provider
    assert registry.list_all() == [provider]

    registry.unregister("fiverr")
    assert registry.get("fiverr") is None
    assert registry.list_all() == []
