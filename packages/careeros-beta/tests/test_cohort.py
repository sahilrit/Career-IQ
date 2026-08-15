"""Tests for the capacity-limited beta invite cohort."""

from __future__ import annotations

import pytest

from careeros_beta import (
    BetaCohortFullError,
    BetaCohortRepository,
    InviteStatus,
    accept_invite,
    invite_to_beta,
    is_admitted,
    revoke_invite,
)


def test_invite_creates_a_pending_invite(store):
    repository = BetaCohortRepository(store)
    invite = invite_to_beta(repository, "ada@example.com", max_seats=10)
    assert invite.status == InviteStatus.PENDING
    assert repository.find_by_email("ada@example.com") == invite


def test_inviting_the_same_email_twice_is_idempotent(store):
    repository = BetaCohortRepository(store)
    first = invite_to_beta(repository, "ada@example.com", max_seats=10)
    second = invite_to_beta(repository, "ada@example.com", max_seats=10)
    assert first.id == second.id


def test_invite_beyond_capacity_raises(store):
    repository = BetaCohortRepository(store)
    invite_to_beta(repository, "one@example.com", max_seats=1)
    with pytest.raises(BetaCohortFullError):
        invite_to_beta(repository, "two@example.com", max_seats=1)


def test_revoked_invite_frees_a_seat(store):
    repository = BetaCohortRepository(store)
    invite_to_beta(repository, "one@example.com", max_seats=1)
    revoke_invite(repository, "one@example.com")
    second = invite_to_beta(repository, "two@example.com", max_seats=1)
    assert second.email == "two@example.com"


def test_accept_invite_marks_it_accepted(store):
    repository = BetaCohortRepository(store)
    invite_to_beta(repository, "ada@example.com", max_seats=10)
    accepted = accept_invite(repository, "ada@example.com")
    assert accepted.status == InviteStatus.ACCEPTED
    assert is_admitted(repository, "ada@example.com") is True


def test_uninvited_email_is_not_admitted(store):
    repository = BetaCohortRepository(store)
    assert is_admitted(repository, "nobody@example.com") is False


def test_pending_invite_is_not_admitted(store):
    repository = BetaCohortRepository(store)
    invite_to_beta(repository, "ada@example.com", max_seats=10)
    assert is_admitted(repository, "ada@example.com") is False


def test_accept_unknown_email_returns_none(store):
    repository = BetaCohortRepository(store)
    assert accept_invite(repository, "nobody@example.com") is None


def test_revoke_unknown_email_returns_none(store):
    repository = BetaCohortRepository(store)
    assert revoke_invite(repository, "nobody@example.com") is None
