"""Tests for RelationshipTimeline / TimelineRepository."""

from __future__ import annotations

from careeros_crm import RelationshipStage


def test_fresh_timeline_has_no_current_stage(timeline_repository):
    timeline = timeline_repository.load("contact-1")
    assert timeline.current_stage is None
    assert timeline.next_stage == RelationshipStage.VIEWED


def test_recording_a_stage_updates_current_and_next(timeline_repository):
    timeline_repository.record("contact-1", RelationshipStage.VIEWED)
    timeline = timeline_repository.load("contact-1")
    assert timeline.current_stage == RelationshipStage.VIEWED
    assert timeline.next_stage == RelationshipStage.LIKED


def test_current_stage_is_the_furthest_reached_regardless_of_recording_order(
    timeline_repository,
):
    timeline_repository.record("contact-1", RelationshipStage.CONVERSATION)
    timeline_repository.record("contact-1", RelationshipStage.VIEWED)
    timeline = timeline_repository.load("contact-1")
    assert timeline.current_stage == RelationshipStage.CONVERSATION


def test_a_relationship_can_skip_stages(timeline_repository):
    timeline_repository.record("contact-1", RelationshipStage.CONVERSATION)
    timeline = timeline_repository.load("contact-1")
    assert len(timeline.interactions) == 1
    assert timeline.current_stage == RelationshipStage.CONVERSATION


def test_recording_the_same_stage_twice_keeps_both_interactions(timeline_repository):
    timeline_repository.record("contact-1", RelationshipStage.VIEWED)
    timeline_repository.record("contact-1", RelationshipStage.VIEWED)
    timeline = timeline_repository.load("contact-1")
    assert len(timeline.interactions) == 2


def test_final_stage_has_no_next_stage(timeline_repository):
    timeline_repository.record("contact-1", RelationshipStage.CLIENT_OR_EMPLOYER)
    timeline = timeline_repository.load("contact-1")
    assert timeline.next_stage is None


def test_timeline_is_isolated_per_contact(timeline_repository):
    timeline_repository.record("contact-1", RelationshipStage.VIEWED)
    other = timeline_repository.load("contact-2")
    assert other.current_stage is None


def test_detail_is_stored_on_the_interaction(timeline_repository):
    timeline_repository.record("contact-1", RelationshipStage.MESSAGED, detail="sent a note")
    timeline = timeline_repository.load("contact-1")
    assert timeline.interactions[-1].detail == "sent a note"
