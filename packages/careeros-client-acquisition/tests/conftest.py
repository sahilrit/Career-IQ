"""Shared fixtures for client acquisition tests."""

from __future__ import annotations

import pytest

from careeros_browser import FakeBrowserSession
from careeros_career_brain import CareerBrain, Identity, Skill
from careeros_client_acquisition import (
    ClientAcquisitionProgressRepository,
    Company,
    CompanyRepository,
)
from careeros_common import DocumentStore
from careeros_opportunity_intelligence import ClientRepository


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


@pytest.fixture
def company_repository(store):
    return CompanyRepository(store)


@pytest.fixture
def progress_repository(store):
    return ClientAcquisitionProgressRepository(store)


@pytest.fixture
def client_repository(store):
    return ClientRepository(store)


@pytest.fixture
def company():
    return Company(name="Widget Co", website="https://widgetco.example.com", industry="retail")


@pytest.fixture
def brain():
    return CareerBrain(
        identity=Identity(full_name="Ada Lovelace", email="ada@example.com", headline="Consultant"),
        skills=[Skill(name="Shopify", proficiency=5), Skill(name="CRO", proficiency=4)],
    )


@pytest.fixture
def fake_session():
    return FakeBrowserSession()
