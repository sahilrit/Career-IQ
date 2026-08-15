"""Shared fixtures for audit/proposal engine tests."""

from __future__ import annotations

import pytest

from careeros_browser import FakeBrowserSession
from careeros_career_brain import CareerBrain, Identity, Skill
from careeros_client_acquisition import Company


@pytest.fixture
def company():
    return Company(name="Widget Co", website="https://widgetco.example.com", industry="retail")


@pytest.fixture
def brain():
    return CareerBrain(
        identity=Identity(
            full_name="Ada Lovelace", email="ada@example.com", headline="CRO Consultant"
        ),
        skills=[Skill(name="Shopify", proficiency=5), Skill(name="CRO", proficiency=4)],
    )


@pytest.fixture
def fake_session():
    return FakeBrowserSession()
