"""Tests for the shared exception hierarchy."""

from __future__ import annotations

import pytest

from careeros_common.exceptions import CareerOSError, ConfigurationError


def test_configuration_error_is_a_careeros_error():
    assert issubclass(ConfigurationError, CareerOSError)


def test_careeros_error_can_be_raised_and_caught_by_the_base_class():
    with pytest.raises(CareerOSError):
        raise ConfigurationError("bad config")
