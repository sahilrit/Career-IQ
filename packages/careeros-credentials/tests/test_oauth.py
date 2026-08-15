"""Tests for OAuthToken lifecycle."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from careeros_credentials import OAuthToken


def test_token_with_no_expiry_is_never_expired():
    token = OAuthToken(access_token="x")
    assert token.is_expired() is False
    assert token.needs_refresh() is False


def test_token_past_expiry_is_expired():
    now = datetime(2026, 1, 1, tzinfo=UTC)
    token = OAuthToken(access_token="x", expires_at=now - timedelta(minutes=1))
    assert token.is_expired(as_of=now) is True


def test_token_before_expiry_is_not_expired():
    now = datetime(2026, 1, 1, tzinfo=UTC)
    token = OAuthToken(access_token="x", expires_at=now + timedelta(hours=1))
    assert token.is_expired(as_of=now) is False


def test_needs_refresh_within_the_buffer_window():
    now = datetime(2026, 1, 1, tzinfo=UTC)
    token = OAuthToken(access_token="x", expires_at=now + timedelta(seconds=100))
    assert token.needs_refresh(buffer_seconds=300, as_of=now) is True


def test_does_not_need_refresh_well_before_expiry():
    now = datetime(2026, 1, 1, tzinfo=UTC)
    token = OAuthToken(access_token="x", expires_at=now + timedelta(hours=1))
    assert token.needs_refresh(buffer_seconds=300, as_of=now) is False


def test_scope_defaults_to_empty_list():
    token = OAuthToken(access_token="x")
    assert token.scope == []
