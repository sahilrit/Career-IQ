"""Shared fixtures for marketplace governance tests."""

from __future__ import annotations

import pytest

from careeros_common import DocumentStore
from careeros_plugin_sdk import PluginManifest


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


@pytest.fixture
def manifest():
    return PluginManifest(
        id="careeros-example",
        name="Example",
        version="1.0.0",
        description="An example plugin.",
        actions=["do_thing"],
    )
