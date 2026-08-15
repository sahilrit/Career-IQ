"""Shared fixtures for workflow builder tests."""

from __future__ import annotations

import pytest

from careeros_common import DocumentStore
from careeros_workflow_builder import CallableActionExecutor, RuleRepository


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


@pytest.fixture
def rule_repository(store):
    return RuleRepository(store)


@pytest.fixture
def executor():
    return CallableActionExecutor()
