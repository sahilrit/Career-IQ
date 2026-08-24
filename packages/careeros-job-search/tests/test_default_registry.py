"""Tests for the default provider registry's composition.

The registry is the one place provider wiring lives, so these tests guard
what a fresh install actually searches — including the sources that can be
switched off without touching code.
"""

from __future__ import annotations

import pytest

from careeros_job_search import default_provider_registry
from careeros_job_search.optional_providers import LINKEDIN_ENV_VAR


@pytest.fixture(autouse=True)
def clear_optional_flags(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv(LINKEDIN_ENV_VAR, raising=False)


def _ids(registry) -> set[str]:
    return {provider.provider_id for provider in registry.list_all()}


def test_the_original_api_backed_providers_are_all_registered():
    ids = _ids(default_provider_registry())
    assert {
        "remoteok",
        "arbeitnow",
        "himalayas",
        "jobicy",
        "workingnomads",
        "weworkremotely",
        "themuse",
        "greenhouse",
        "ashby",
        "lever",
        "hiringcafe",
        "adzuna",
    } <= ids


def test_linkedin_is_registered_by_default():
    assert "linkedin" in _ids(default_provider_registry())


def test_linkedin_can_be_switched_off(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(LINKEDIN_ENV_VAR, "0")
    assert "linkedin" not in _ids(default_provider_registry())


def test_switching_linkedin_off_leaves_the_rest_alone(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(LINKEDIN_ENV_VAR, "0")
    assert "remoteok" in _ids(default_provider_registry())


def test_every_provider_id_is_unique():
    registry = default_provider_registry()
    ids = [provider.provider_id for provider in registry.list_all()]
    assert len(ids) == len(set(ids))
