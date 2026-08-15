"""Tests for MeetingNote / MeetingNoteRepository."""

from __future__ import annotations

from careeros_client_success import MeetingNote


def test_list_for_client_filters(meeting_note_repository):
    matching = MeetingNote(client_id="client-1", summary="Kickoff call", action_items=["Send NDA"])
    other = MeetingNote(client_id="client-2", summary="Unrelated")
    meeting_note_repository.save(matching)
    meeting_note_repository.save(other)
    assert meeting_note_repository.list_for_client("client-1") == [matching]
