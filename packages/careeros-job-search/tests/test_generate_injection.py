"""generate_application_for_job accepts an injected cover-letter generator
(the seam the API uses to swap in real AI)."""

from __future__ import annotations

import pytest

from careeros_career_brain import CareerBrain, CareerBrainRepository, Identity
from careeros_common import open_store
from careeros_job_discovery import JobPostingRepository
from careeros_job_providers import JobPosting
from careeros_job_search import generate_application_for_job


class FakeGen:
    def generate(self, brain, posting):
        return "INJECTED"


@pytest.fixture
def seeded(tmp_path, monkeypatch):
    monkeypatch.setenv("CAREEROS_DATA_DIR", str(tmp_path))
    store = open_store()
    brain = CareerBrain(identity=Identity(full_name="Ada Lovelace", email="a@x.com"))
    CareerBrainRepository(store).save(brain)
    posting = JobPosting(
        source_provider="test",
        external_id="1",
        title="PPC Manager",
        company_name="Acme",
        url="https://acme.com/j/1",
        description="Run paid campaigns.",
    )
    JobPostingRepository(store).save(posting)
    return store, brain.identity.id, posting.url


def test_generate_uses_injected_cover_letter_generator(seeded):
    store, identity_id, job_url = seeded
    package = generate_application_for_job(
        store, identity_id, job_url, cover_letter_generator=FakeGen()
    )
    assert package is not None
    assert package.cover_letter == "INJECTED"


def test_generate_defaults_to_template(seeded):
    store, identity_id, job_url = seeded
    package = generate_application_for_job(store, identity_id, job_url)
    assert package is not None
    assert "Acme" in package.cover_letter  # template still fills company
