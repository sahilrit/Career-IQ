"""Tests for the BetaDivision facade."""

from __future__ import annotations

import pytest

from careeros_beta import BetaCohortFullError, BetaDivision


def test_check_readiness_reflects_the_real_installed_workspace(store):
    division = BetaDivision(store)
    report = division.check_readiness()
    assert report.is_ready is True


def test_invite_accept_and_admission_flow(store):
    division = BetaDivision(store, max_seats=5)
    division.invite("ada@example.com")
    assert division.is_admitted("ada@example.com") is False
    division.accept("ada@example.com")
    assert division.is_admitted("ada@example.com") is True


def test_seats_remaining_decreases_as_invites_are_sent(store):
    division = BetaDivision(store, max_seats=2)
    assert division.seats_remaining() == 2
    division.invite("one@example.com")
    assert division.seats_remaining() == 1
    division.invite("two@example.com")
    assert division.seats_remaining() == 0
    with pytest.raises(BetaCohortFullError):
        division.invite("three@example.com")


def test_revoke_frees_a_seat(store):
    division = BetaDivision(store, max_seats=1)
    division.invite("one@example.com")
    assert division.seats_remaining() == 0
    division.revoke("one@example.com")
    assert division.seats_remaining() == 1
