"""Tests for password/session security policy checks."""

from __future__ import annotations

from careeros_compliance import SecurityPolicy, check_password


def test_password_meeting_every_requirement_has_no_violations():
    policy = SecurityPolicy()
    assert check_password("Str0ng!Passw0rd", policy) == []


def test_password_too_short_is_flagged():
    policy = SecurityPolicy(min_length=12)
    violations = check_password("Sh0rt!", policy)
    assert any("12 characters" in violation for violation in violations)


def test_password_missing_uppercase_is_flagged():
    policy = SecurityPolicy()
    violations = check_password("weakpassw0rd!", policy)
    assert any("uppercase" in violation for violation in violations)


def test_password_missing_digit_is_flagged():
    policy = SecurityPolicy()
    violations = check_password("NoDigitsHere!", policy)
    assert any("digit" in violation for violation in violations)


def test_password_missing_symbol_is_flagged():
    policy = SecurityPolicy()
    violations = check_password("NoSymbolsHere1", policy)
    assert any("symbol" in violation for violation in violations)


def test_relaxed_policy_skips_disabled_requirements():
    policy = SecurityPolicy(
        min_length=4, require_uppercase=False, require_digit=False, require_symbol=False
    )
    assert check_password("weak", policy) == []


def test_default_policy_requires_mfa_is_false():
    assert SecurityPolicy().mfa_required is False
