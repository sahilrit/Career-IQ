"""Skills claimed with no source support must not answer screening questions.

``QuestionAnswerer`` answers "do you have experience with X?" by checking X
against the skill list. A skill nobody can support therefore does not sit there
harmlessly — it actively produces a "Yes" to an employer.

SEO and Google Analytics were both in the Career Brain: SEO appears nowhere in
Sahil's source documents, and Google Analytics is on the do-not-add list in his
own UPLERS_PROFILE.md §3 (the GA version was never verified).
"""

from __future__ import annotations

import pytest

from careeros_application_engine import QuestionAnswerer
from careeros_career_brain import CareerBrain, Identity, Skill
from careeros_job_providers import JobPosting

#: Claimed in the Career Brain, supported by nothing in the job hunt folder.
REMOVED_SKILLS = ["SEO", "Google Analytics"]

#: On the do-not-claim list in SAHIL_MASTER_PROFILE.md §4 / UPLERS §3. None of
#: these may ever answer "yes" to an experience question.
NEVER_CLAIM = [
    "SEO",
    "Google Analytics",
    "GA4",
    "Google Ads",
    "TikTok Ads",
    "Klaviyo",
    "Amazon Ads",
    "Snapchat Ads",
]


@pytest.fixture
def brain() -> CareerBrain:
    """The audited skill set — what the source documents actually support."""
    return CareerBrain(
        identity=Identity(full_name="Sahil Sachdeva", email="s@example.com"),
        skills=[
            Skill(name="Meta Ads"),
            Skill(name="Paid Social"),
            Skill(name="Shopify"),
            Skill(name="Google Tag Manager"),
            Skill(name="Media Buying"),
            Skill(name="Performance Marketing"),
        ],
    )


@pytest.fixture
def posting() -> JobPosting:
    return JobPosting(
        source_provider="test",
        external_id="1",
        title="Performance Marketing Manager",
        company_name="Globex",
        url="https://example.test/1",
    )


class TestRemovedSkillsDoNotAnswerYes:
    @pytest.mark.parametrize("skill", REMOVED_SKILLS)
    def test_a_removed_skill_does_not_produce_a_yes(self, brain, posting, skill):
        answer = QuestionAnswerer(brain, posting).answer(f"Do you have experience with {skill}?")
        assert answer.choice != "yes"
        assert answer.text.lower() != "yes"

    @pytest.mark.parametrize("skill", NEVER_CLAIM)
    def test_nothing_on_the_do_not_claim_list_produces_a_yes(self, brain, posting, skill):
        answer = QuestionAnswerer(brain, posting).answer(f"Do you have experience with {skill}?")
        assert answer.choice != "yes", skill

    def test_a_removed_skill_becomes_a_question_for_the_user(self, brain, posting):
        # Not silently "no" either — CareerOS does not answer for him.
        answer = QuestionAnswerer(brain, posting).answer("Do you have experience with SEO?")
        assert answer.needs_user_input


class TestSupportedSkillsStillWork:
    """Removing the unsupported ones must not blunt the real ones."""

    @pytest.mark.parametrize("skill", ["Meta Ads", "Shopify", "Google Tag Manager"])
    def test_a_documented_skill_still_answers_yes(self, brain, posting, skill):
        answer = QuestionAnswerer(brain, posting).answer(f"Do you have experience with {skill}?")
        assert answer.choice == "yes", skill

    def test_google_tag_manager_is_not_confused_with_google_ads(self, brain, posting):
        # Both start with "Google". GTM is documented; Google Ads is a gap with
        # under $120 of lifetime spend.
        gtm = QuestionAnswerer(brain, posting).answer("Experience with Google Tag Manager?")
        ads = QuestionAnswerer(brain, posting).answer("Experience with Google Ads?")
        assert gtm.choice == "yes"
        assert ads.choice != "yes"


class TestJobTitlesAreNotSkills:
    """ "PPC Manager" was stored in the skills list.

    A job title in that list is not inert. ``_has_skill`` matches skill names
    against screening questions, so it would answer "yes" to "do you have
    experience with PPC Manager?" — and it renders on the résumé's skills line
    as if it were a competency. The underlying competency is already covered by
    Performance Marketing, Paid Social and Media Buying.
    """

    @pytest.mark.parametrize(
        "title",
        # Titles that have appeared, or plausibly could appear, in a skills
        # list because they were imported from a résumé's job history.
        [
            "PPC Manager",
            "Performance Marketing Consultant",
            "Freelance Performance Marketer",
            "Marketing Manager",
            "Growth Marketing Lead",
        ],
    )
    def test_a_job_title_is_not_offered_as_a_skill(self, brain, title):
        # The fixture is the audited skill set; no title may be in it.
        assert title.lower() not in {s.name.lower() for s in brain.skills}, title

    def test_a_title_in_the_skills_list_would_wrongly_answer_yes(self, brain, posting):
        # Demonstrates WHY this matters, so the guard above is not mistaken for
        # cosmetic tidying.
        from careeros_career_brain import Skill

        polluted = brain.model_copy(deep=True)
        polluted.skills.append(Skill(name="PPC Manager"))
        answer = QuestionAnswerer(polluted, posting).answer(
            "Do you have experience with PPC Manager?"
        )
        assert answer.choice == "yes"  # the bug, reproduced

        clean = QuestionAnswerer(brain, posting).answer("Do you have experience with PPC Manager?")
        assert clean.choice != "yes"  # and its absence, fixed

    def test_the_real_competency_is_still_claimable(self, brain, posting):
        # Removing the title must not cost him the underlying skill.
        for skill in ("Performance Marketing", "Paid Social", "Media Buying"):
            assert skill.lower() in {s.name.lower() for s in brain.skills}, skill
