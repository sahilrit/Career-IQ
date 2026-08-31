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


def test_the_aggregator_providers_are_all_registered():
    ids = _ids(default_provider_registry())
    assert {
        "remoteok",
        "arbeitnow",
        "himalayas",
        "jobicy",
        "workingnomads",
        "weworkremotely",
        "themuse",
        "hiringcafe",
        "adzuna",
        "golangjobs",
        "seek",
    } <= ids


def test_every_hosted_ats_is_registered():
    """The ATS sources are what the application engine can actually fill, so
    losing one silently is a much bigger regression than losing an aggregator.
    Ids are namespaced ``ats:<name>`` so an ATS can never collide with an
    aggregator of the same name."""
    ids = _ids(default_provider_registry())
    assert {
        "ats:greenhouse",
        "ats:lever",
        "ats:ashby",
        "ats:smartrecruiters",
        "ats:workable",
        "ats:recruitee",
        "ats:personio",
        "ats:bamboohr",
        "ats:workday",
    } <= ids


def test_every_registered_ats_provider_has_boards_to_crawl():
    # An ATS provider with no boards can never return anything; registering one
    # would put a permanently-silent source in every search.
    from careeros_ats_providers import AtsBoardProvider

    for provider in default_provider_registry().list_all():
        if isinstance(provider, AtsBoardProvider):
            assert provider.boards, f"{provider.provider_id} has no boards"


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
