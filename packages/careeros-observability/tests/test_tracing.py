"""Tests for Tracer."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from careeros_observability import Tracer


def _clock_sequence(start: datetime, step: timedelta):
    current = {"value": start}

    def _clock() -> datetime:
        value = current["value"]
        current["value"] = value + step
        return value

    return _clock


def test_span_records_start_and_end_time():
    clock = _clock_sequence(datetime(2026, 1, 1, tzinfo=UTC), timedelta(seconds=2))
    tracer = Tracer(clock=clock)
    with tracer.span("apply_to_job") as span:
        assert span.ended_at is None
    assert span.started_at == datetime(2026, 1, 1, tzinfo=UTC)
    assert span.ended_at == datetime(2026, 1, 1, 0, 0, 2, tzinfo=UTC)
    assert span.duration_seconds == 2.0


def test_nested_span_records_parent_id():
    tracer = Tracer()
    with tracer.span("outer") as outer, tracer.span("inner") as inner:
        assert inner.parent_span_id == outer.span_id
    assert outer.parent_span_id is None


def test_span_attributes_are_stored():
    tracer = Tracer()
    with tracer.span("discover_jobs", provider="remoteok") as span:
        assert span.attributes == {"provider": "remoteok"}


def test_spans_returns_every_recorded_span_in_order():
    tracer = Tracer()
    with tracer.span("first"):
        pass
    with tracer.span("second"):
        pass
    names = [span.name for span in tracer.spans()]
    assert names == ["first", "second"]


def test_span_ends_even_when_body_raises():
    tracer = Tracer()
    try:
        with tracer.span("risky") as span:
            raise ValueError("boom")
    except ValueError:
        pass
    assert span.ended_at is not None
