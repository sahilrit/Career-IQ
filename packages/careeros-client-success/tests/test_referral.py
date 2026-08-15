"""Tests for ReferralRecord / ReferralRepository."""

from __future__ import annotations

from careeros_client_success import ReferralRecord


def test_list_for_client_filters(referral_repository):
    matching = ReferralRecord(client_id="client-1", referred_name="New Prospect Co")
    other = ReferralRecord(client_id="client-2", referred_name="Unrelated Co")
    referral_repository.save(matching)
    referral_repository.save(other)
    assert referral_repository.list_for_client("client-1") == [matching]
