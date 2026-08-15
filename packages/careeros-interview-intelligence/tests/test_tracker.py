"""Tests for BriefingTracker."""

from __future__ import annotations

import pytest

from careeros_common import DocumentStore
from careeros_interview_intelligence import BriefingMilestone, BriefingTracker


@pytest.fixture
def tracker():
    with DocumentStore() as store:
        yield BriefingTracker(store)


def test_no_milestones_fired_initially(tracker):
    assert tracker.fired_milestones("event-1") == set()


def test_mark_fired_persists(tracker):
    tracker.mark_fired("event-1", BriefingMilestone.H48)
    assert tracker.fired_milestones("event-1") == {BriefingMilestone.H48}


def test_multiple_milestones_accumulate(tracker):
    tracker.mark_fired("event-1", BriefingMilestone.H48)
    tracker.mark_fired("event-1", BriefingMilestone.H24)
    assert tracker.fired_milestones("event-1") == {BriefingMilestone.H48, BriefingMilestone.H24}


def test_tracking_is_isolated_per_event(tracker):
    tracker.mark_fired("event-1", BriefingMilestone.H48)
    assert tracker.fired_milestones("event-2") == set()
