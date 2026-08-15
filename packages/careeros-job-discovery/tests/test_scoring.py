"""Tests for the heuristic job/Career-Brain match score."""

from __future__ import annotations

import pytest

from careeros_career_brain import Preferences
from careeros_job_discovery import score_posting
from careeros_job_providers import Salary


def test_perfect_match_scores_close_to_one(brain_factory, posting_factory):
    brain = brain_factory(
        preferences=Preferences(
            desired_titles=["Python Engineer"], remote_only=True, min_salary=100_000
        )
    )
    posting = posting_factory(
        title="Senior Python Engineer",
        remote=True,
        salary=Salary(min_amount=120_000, max_amount=150_000),
    )
    assert score_posting(posting, brain) > 0.9


def test_no_skill_overlap_scores_lower_than_full_overlap(brain_factory, posting_factory):
    brain = brain_factory()
    matching = posting_factory(tags=["python", "django"], description="", title="Engineer")
    non_matching = posting_factory(tags=["rust", "erlang"], description="", title="Engineer")
    assert score_posting(matching, brain) > score_posting(non_matching, brain)


def test_no_stated_title_preference_does_not_penalize():
    from careeros_career_brain import CareerBrain, Identity

    brain = CareerBrain(identity=Identity(full_name="Ada", email="ada@example.com"))
    from careeros_job_providers import JobPosting

    posting = JobPosting(
        source_provider="remoteok",
        external_id="1",
        title="Anything At All",
        company_name="Acme",
        url="https://example.com/1",
    )
    # No skills, no preferences at all: title/salary/location components are
    # all neutral (1.0), only the skill component (0.0, no skills) drags
    # the score down — proving title absence isn't itself penalized.
    assert score_posting(posting, brain) == pytest.approx(0.5)


def test_remote_only_preference_zeroes_out_non_remote_postings(brain_factory, posting_factory):
    brain = brain_factory(preferences=Preferences(remote_only=True))
    posting = posting_factory(remote=False)
    with_remote = posting_factory(remote=True)
    assert score_posting(posting, brain) < score_posting(with_remote, brain)


def test_salary_below_minimum_scores_lower_than_salary_above(brain_factory, posting_factory):
    brain = brain_factory(preferences=Preferences(min_salary=150_000))
    low = posting_factory(salary=Salary(min_amount=80_000, max_amount=90_000))
    high = posting_factory(salary=Salary(min_amount=160_000, max_amount=180_000))
    assert score_posting(low, brain) < score_posting(high, brain)


def test_score_is_always_between_zero_and_one(brain_factory, posting_factory):
    brain = brain_factory(
        preferences=Preferences(
            desired_titles=["Nothing Like This"], remote_only=True, min_salary=1_000_000
        )
    )
    posting = posting_factory(remote=False, tags=[], title="Completely Unrelated Role")
    score = score_posting(posting, brain)
    assert 0.0 <= score <= 1.0
