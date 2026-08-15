"""Tests for EventBus publish/subscribe dispatch."""

from __future__ import annotations

from careeros_event_bus import Event, EventBus


def test_subscriber_receives_matching_event():
    bus = EventBus()
    received = []
    bus.subscribe("job.discovered", received.append)

    bus.publish(Event(event_type="job.discovered", payload={"job_id": "1"}))

    assert len(received) == 1
    assert received[0].payload["job_id"] == "1"


def test_subscriber_does_not_receive_non_matching_event():
    bus = EventBus()
    received = []
    bus.subscribe("job.discovered", received.append)

    bus.publish(Event(event_type="application.status_changed"))

    assert received == []


def test_wildcard_pattern_matches_whole_namespace():
    bus = EventBus()
    received = []
    bus.subscribe("job.*", received.append)

    bus.publish(Event(event_type="job.discovered"))
    bus.publish(Event(event_type="job.scored"))
    bus.publish(Event(event_type="application.status_changed"))

    assert [e.event_type for e in received] == ["job.discovered", "job.scored"]


def test_star_pattern_matches_everything():
    bus = EventBus()
    received = []
    bus.subscribe("*", received.append)

    bus.publish(Event(event_type="job.discovered"))
    bus.publish(Event(event_type="anything.else"))

    assert len(received) == 2


def test_multiple_subscribers_all_receive_the_event():
    bus = EventBus()
    first, second = [], []
    bus.subscribe("job.discovered", first.append)
    bus.subscribe("job.discovered", second.append)

    bus.publish(Event(event_type="job.discovered"))

    assert len(first) == 1
    assert len(second) == 1


def test_a_failing_handler_does_not_stop_other_handlers_or_raise():
    bus = EventBus()
    received = []

    def broken_handler(event: Event) -> None:
        raise RuntimeError("boom")

    bus.subscribe("job.discovered", broken_handler)
    bus.subscribe("job.discovered", received.append)

    bus.publish(Event(event_type="job.discovered"))  # must not raise

    assert len(received) == 1


def test_unsubscribe_stops_future_delivery():
    bus = EventBus()
    received = []
    bus.subscribe("job.discovered", received.append)
    bus.unsubscribe("job.discovered", received.append)

    bus.publish(Event(event_type="job.discovered"))

    assert received == []


def test_history_returns_every_published_event_in_order():
    bus = EventBus()
    bus.publish(Event(event_type="job.discovered"))
    bus.publish(Event(event_type="job.scored"))

    assert [e.event_type for e in bus.history()] == ["job.discovered", "job.scored"]


def test_history_can_be_filtered_by_pattern():
    bus = EventBus()
    bus.publish(Event(event_type="job.discovered"))
    bus.publish(Event(event_type="application.status_changed"))

    assert [e.event_type for e in bus.history("job.*")] == ["job.discovered"]
