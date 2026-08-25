"""Tests for disqualifying_requirement — skip a job only when it EXPLICITLY
rules the candidate out, never on a guess."""

from __future__ import annotations

import pytest

from careeros_application_engine import disqualifying_requirement
from careeros_career_brain import CareerBrain, Identity, Preferences


def _brain(**prefs) -> CareerBrain:
    return CareerBrain(
        identity=Identity(
            full_name="Sahil Sachdeva",
            email="s@example.com",
            location=prefs.pop("location", "India (Remote)"),
        ),
        preferences=Preferences(**prefs),
    )


# --- sponsorship ---------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "We are unable to sponsor visas for this position.",
        "This role does not offer visa sponsorship.",
        "No sponsorship available.",
        "Candidates must be able to work without sponsorship.",
        "We cannot sponsor work visas.",
    ],
)
def test_sponsorship_needed_and_role_refuses_it_is_skipped(text):
    brain = _brain(needs_visa_sponsorship=True)
    assert disqualifying_requirement(brain, text) is not None


def test_sponsorship_language_ignored_when_candidate_does_not_need_it():
    brain = _brain(needs_visa_sponsorship=False)
    assert disqualifying_requirement(brain, "No visa sponsorship available.") is None


# --- US work authorization ----------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "Must be authorized to work in the United States.",
        "US work authorization is required.",
        "Must be a US citizen.",
        "This position requires an active security clearance.",
        "Applicants must be legally eligible to work in the U.S.",
    ],
)
def test_us_auth_required_and_candidate_lacks_it_is_skipped(text):
    brain = _brain(us_work_authorized=False)
    assert disqualifying_requirement(brain, text) is not None


def test_us_auth_language_ignored_when_candidate_is_authorized():
    brain = _brain(us_work_authorized=True)
    assert disqualifying_requirement(brain, "Must be authorized to work in the US.") is None


# --- US-only location ----------------------------------------------------


def test_us_only_location_is_skipped_for_a_non_us_remote_candidate():
    brain = _brain(remote_only=True, location="India (Remote)")
    assert disqualifying_requirement(brain, "Open to US-based candidates only.") is not None


def test_us_only_location_not_flagged_for_a_us_based_candidate():
    brain = _brain(remote_only=True, us_work_authorized=True, location="Austin, United States")
    assert disqualifying_requirement(brain, "US-based candidates only.") is None


# --- conservatism: don't over-filter ------------------------------------


def test_soft_preference_is_not_a_disqualifier():
    brain = _brain(needs_visa_sponsorship=True, us_work_authorized=False)
    text = "Remote role, US time zone preferred. Global team welcome."
    assert disqualifying_requirement(brain, text) is None


def test_plain_marketing_jd_is_not_disqualifying():
    brain = _brain(needs_visa_sponsorship=True, us_work_authorized=False)
    text = "We're hiring a Performance Marketer to scale paid social across Meta and Google."
    assert disqualifying_requirement(brain, text) is None


def test_empty_text_returns_none():
    brain = _brain(us_work_authorized=False, needs_visa_sponsorship=True)
    assert disqualifying_requirement(brain, None, "", "   ") is None


def test_reason_mentions_the_blocker():
    brain = _brain(needs_visa_sponsorship=True)
    reason = disqualifying_requirement(brain, "We do not offer sponsorship.")
    assert reason and "sponsor" in reason.lower()


def test_line_broken_requirement_still_matches():
    brain = _brain(us_work_authorized=False)
    text = "You must be authorized to\n   work in the United States."
    assert disqualifying_requirement(brain, text) is not None
