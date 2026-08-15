"""Tests for the minimal semver constraint matcher."""

from __future__ import annotations

import pytest

from careeros_plugin_sdk import satisfies
from careeros_plugin_sdk.exceptions import PluginValidationError


def test_exact_match():
    assert satisfies("1.2.3", "1.2.3")
    assert not satisfies("1.2.4", "1.2.3")


def test_caret_allows_same_major_greater_or_equal():
    assert satisfies("1.2.3", "^1.0.0")
    assert satisfies("1.9.9", "^1.0.0")
    assert not satisfies("2.0.0", "^1.0.0")
    assert not satisfies("0.9.0", "^1.0.0")


def test_caret_on_zero_major_locks_minor_too():
    assert satisfies("0.2.5", "^0.2.0")
    assert not satisfies("0.3.0", "^0.2.0")


def test_gte_constraint():
    assert satisfies("2.0.0", ">=1.5.0")
    assert satisfies("1.5.0", ">=1.5.0")
    assert not satisfies("1.4.9", ">=1.5.0")


def test_invalid_version_string_raises():
    with pytest.raises(PluginValidationError):
        satisfies("not-a-version", "^1.0.0")
