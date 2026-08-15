"""Tests for run_with_human_fallback / resume: the full AI executes ->
problem detected -> human takeover -> human resolves -> AI resumes flow.
"""

from __future__ import annotations

import pytest

from careeros_browser import FakeBrowserSession
from careeros_event_bus import EventBus
from careeros_human_in_the_loop import (
    HandoffSession,
    SelectorAppearsDetector,
    resume,
    run_with_human_fallback,
)


def test_clean_run_executes_the_action_and_completes(tmp_path):
    session = FakeBrowserSession()
    handoff = HandoffSession("task-1", EventBus())

    result = run_with_human_fallback(session, lambda: "done", [], handoff)

    assert result.completed is True
    assert result.value == "done"
    assert result.needs_human is False
    assert not handoff.is_awaiting_human


def test_detector_flags_a_problem_before_the_action_runs():
    session = FakeBrowserSession()
    session.set_visible("#captcha")
    handoff = HandoffSession("task-1", EventBus())
    calls = []

    detectors = [SelectorAppearsDetector("#captcha", kind="captcha")]
    result = run_with_human_fallback(session, lambda: calls.append(1), detectors, handoff)

    assert result.completed is False
    assert result.needs_human is True
    assert calls == []  # action never ran
    assert handoff.is_awaiting_human
    assert handoff.records[-1].problem.kind == "captcha"


def test_action_raising_triggers_a_handoff_instead_of_propagating():
    session = FakeBrowserSession()
    handoff = HandoffSession("task-1", EventBus())

    def broken_action():
        raise RuntimeError("unexpected page state")

    result = run_with_human_fallback(session, broken_action, [], handoff)

    assert result.completed is False
    assert result.needs_human is True
    assert "unexpected page state" in handoff.records[-1].problem.description


def test_handoff_takes_a_screenshot_when_a_path_is_given(tmp_path):
    session = FakeBrowserSession()
    session.set_visible("#captcha")
    handoff = HandoffSession("task-1", EventBus())

    run_with_human_fallback(
        session,
        lambda: None,
        [SelectorAppearsDetector("#captcha")],
        handoff,
        screenshot_path=tmp_path / "shot.png",
    )

    assert session.screenshots_taken == [tmp_path / "shot.png"]
    assert handoff.records[-1].screenshot == tmp_path / "shot.png"


def test_resume_before_resolution_raises():
    session = FakeBrowserSession()
    session.set_visible("#captcha")
    handoff = HandoffSession("task-1", EventBus())
    run_with_human_fallback(session, lambda: None, [SelectorAppearsDetector("#captcha")], handoff)

    with pytest.raises(ValueError, match="not RUNNING"):
        resume(session, lambda: None, [SelectorAppearsDetector("#captcha")], handoff)


def test_resume_after_human_resolves_the_underlying_problem_succeeds():
    session = FakeBrowserSession()
    session.set_visible("#captcha")
    handoff = HandoffSession("task-1", EventBus())
    detectors = [SelectorAppearsDetector("#captcha")]

    first = run_with_human_fallback(session, lambda: "value", detectors, handoff)
    assert first.needs_human is True

    # A human solves the captcha out of band, then signals resolution.
    session.set_hidden("#captcha")
    handoff.resolve(note="solved manually")

    second = resume(session, lambda: "value", detectors, handoff)

    assert second.completed is True
    assert second.value == "value"
