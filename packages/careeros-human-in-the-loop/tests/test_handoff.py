"""Tests for HandoffSession's state machine and published events."""

from __future__ import annotations

from pathlib import Path

import pytest

from careeros_event_bus import EventBus
from careeros_human_in_the_loop import HandoffSession, HandoffState, Problem


def test_starts_in_running_state():
    handoff = HandoffSession("task-1", EventBus())
    assert handoff.state == HandoffState.RUNNING
    assert not handoff.is_awaiting_human


def test_request_takeover_moves_to_awaiting_human_and_publishes_event():
    bus = EventBus()
    handoff = HandoffSession("task-1", bus)

    handoff.request_takeover(Problem(kind="captcha", description="A captcha appeared"))

    assert handoff.is_awaiting_human
    events = [e for e in bus.history() if e.event_type == "handoff.requested"]
    assert len(events) == 1
    assert events[0].payload["kind"] == "captcha"


def test_request_takeover_records_the_screenshot_path():
    handoff = HandoffSession("task-1", EventBus())
    handoff.request_takeover(
        Problem(kind="captcha", description="x"), screenshot=Path("/tmp/shot.png")
    )
    assert handoff.records[-1].screenshot == Path("/tmp/shot.png")


def test_resolve_moves_back_to_running_and_publishes_event():
    bus = EventBus()
    handoff = HandoffSession("task-1", bus)
    handoff.request_takeover(Problem(kind="captcha", description="x"))

    handoff.resolve(note="solved it manually")

    assert handoff.state == HandoffState.RUNNING
    assert handoff.records[-1].resolution_note == "solved it manually"
    events = [e for e in bus.history() if e.event_type == "handoff.resolved"]
    assert len(events) == 1


def test_resolve_without_a_pending_handoff_raises():
    handoff = HandoffSession("task-1", EventBus())
    with pytest.raises(ValueError, match="Cannot resolve"):
        handoff.resolve()


def test_abandon_moves_to_abandoned_and_publishes_event():
    bus = EventBus()
    handoff = HandoffSession("task-1", bus)
    handoff.request_takeover(Problem(kind="captcha", description="x"))

    handoff.abandon(reason="site permanently blocked")

    assert handoff.state == HandoffState.ABANDONED
    events = [e for e in bus.history() if e.event_type == "handoff.abandoned"]
    assert events[0].payload["reason"] == "site permanently blocked"
