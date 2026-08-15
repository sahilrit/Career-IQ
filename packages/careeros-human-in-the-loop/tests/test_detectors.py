"""Tests for problem detectors, against FakeBrowserSession."""

from __future__ import annotations

from careeros_browser import FakeBrowserSession
from careeros_human_in_the_loop import (
    SelectorAppearsDetector,
    SelectorMissingDetector,
    run_detectors,
)


def test_selector_appears_detector_flags_when_visible():
    session = FakeBrowserSession()
    session.set_visible("#captcha")
    detector = SelectorAppearsDetector("#captcha", kind="captcha")

    problem = detector.detect(session)

    assert problem is not None
    assert problem.kind == "captcha"


def test_selector_appears_detector_is_clean_when_not_visible():
    session = FakeBrowserSession()
    detector = SelectorAppearsDetector("#captcha")
    assert detector.detect(session) is None


def test_selector_missing_detector_flags_when_absent():
    session = FakeBrowserSession()
    detector = SelectorMissingDetector("#success-banner")
    problem = detector.detect(session)
    assert problem is not None
    assert "missing" in problem.kind


def test_selector_missing_detector_is_clean_when_present():
    session = FakeBrowserSession()
    session.set_visible("#success-banner")
    detector = SelectorMissingDetector("#success-banner")
    assert detector.detect(session) is None


def test_run_detectors_returns_first_problem_found():
    session = FakeBrowserSession()
    session.set_visible("#captcha")
    detectors = [
        SelectorAppearsDetector("#captcha", kind="captcha"),
        SelectorMissingDetector("#success-banner"),
    ]
    problem = run_detectors(session, detectors)
    assert problem.kind == "captcha"


def test_run_detectors_returns_none_when_all_clean():
    session = FakeBrowserSession()
    session.set_visible("#success-banner")
    detectors = [
        SelectorAppearsDetector("#captcha"),
        SelectorMissingDetector("#success-banner"),
    ]
    assert run_detectors(session, detectors) is None
