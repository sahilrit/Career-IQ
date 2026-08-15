"""Tests for MetricsRegistry."""

from __future__ import annotations

from careeros_observability import MetricsRegistry


def test_increment_counter_defaults_to_one():
    registry = MetricsRegistry()
    registry.increment_counter("jobs_discovered")
    registry.increment_counter("jobs_discovered")
    assert registry.snapshot().counters["jobs_discovered"] == 2.0


def test_increment_counter_accepts_a_custom_value():
    registry = MetricsRegistry()
    registry.increment_counter("revenue", 500.0)
    registry.increment_counter("revenue", 250.0)
    assert registry.snapshot().counters["revenue"] == 750.0


def test_set_gauge_overwrites_the_previous_value():
    registry = MetricsRegistry()
    registry.set_gauge("queue_depth", 5.0)
    registry.set_gauge("queue_depth", 3.0)
    assert registry.snapshot().gauges["queue_depth"] == 3.0


def test_record_timer_computes_stats():
    registry = MetricsRegistry()
    registry.record_timer("apply_duration", 1.0)
    registry.record_timer("apply_duration", 3.0)
    stats = registry.snapshot().timers["apply_duration"]
    assert stats.count == 2
    assert stats.total_seconds == 4.0
    assert stats.mean_seconds == 2.0
    assert stats.max_seconds == 3.0


def test_snapshot_of_empty_registry_has_no_entries():
    snapshot = MetricsRegistry().snapshot()
    assert snapshot.counters == {}
    assert snapshot.gauges == {}
    assert snapshot.timers == {}
