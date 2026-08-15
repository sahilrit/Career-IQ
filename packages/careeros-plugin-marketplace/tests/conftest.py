"""Shared fixtures for plugin marketplace tests."""

from __future__ import annotations

import pytest

from careeros_plugin_marketplace import SEED_CATALOG


@pytest.fixture
def catalog():
    return list(SEED_CATALOG)
