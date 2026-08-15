"""Shared fixtures for observability tests."""

from __future__ import annotations

import pytest

from careeros_common import DocumentStore


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store
