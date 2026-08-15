"""Tests for the shared logging setup."""

from __future__ import annotations

import logging

from careeros_common.logging import configure_logging, get_logger


def test_get_logger_returns_a_logger_with_the_requested_name():
    assert get_logger("careeros.test").name == "careeros.test"


def test_configure_logging_is_idempotent():
    root = logging.getLogger()
    before = len(root.handlers)
    configure_logging()
    configure_logging()
    after = len(root.handlers)
    assert after - before <= 1
