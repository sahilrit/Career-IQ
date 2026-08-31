"""An unanswerable question is returned as a question, never as an invention.

Two rules this file enforces:

* CareerOS never fabricates an answer. A visa status, a salary expectation or
  an employer it does not know is handed back to the user.
* Handing it back is only useful if it says WHY and WHAT WOULD FIX IT. "Left
  for a human" with no reason is how these became invisible.
"""

from __future__ import annotations

import pytest

from careeros_application_engine import (
    Confidence,
    QuestionAnswerer,
    memory_key_for,
    remember_answer,
)
from careeros_career_brain import (
    Achievement,
    CareerBrain,
    Experience,
    Identity,
    Preferences,
    Skill,
)
from careeros_job_providers import JobPosting


@pytest.fixture
def brain():
    return CareerBrain(
        identity=Identity(
            full_name="Ada Lovelace",
            email="ada@example.com",
            phone="+44 20 7946 0000",
            location="London, UK",
            headline="Growth marketer",
            summary="Performance marketer.",
            links={"linkedin": "https://linkedin.com/in/ada"},
        ),
        experiences=[
            Experience(
                company_name="Acme",
                title="Growth Lead",
                start_date="2020-01-01",
                is_current=True,
                achievements=[Achievement(description="Ran paid acquisition")],
            )
        ],
        skills=[Skill(name="Google Ads", years_experience=5)],
        preferences=Preferences(),
    )


@pytest.fixture
def posting():
    return JobPosting(
        source_provider="test",
        external_id="1",
        title="Performance Marketing Manager",
        company_name="Globex",
        url="https://example.test/job",
    )


class TestNeverInvents:
    def test_work_authorization_is_never_guessed(self, brain, posting):
        # The single most dangerous question to guess: a wrong answer here is
        # a false statement on a legal document.
        answer = QuestionAnswerer(brain, posting).answer("Are you authorized to work in the US?")
        assert answer.needs_user_input
        assert answer.text == ""
        assert answer.confidence is Confidence.UNKNOWN

    def test_sponsorship_is_never_guessed(self, brain, posting):
        answer = QuestionAnswerer(brain, posting).answer("Will you require visa sponsorship?")
        assert answer.needs_user_input
        assert answer.text == ""

    def test_a_stored_preference_is_used_rather_than_left_unknown(self, brain, posting):
        brain.preferences.us_work_authorized = True
        answer = QuestionAnswerer(brain, posting).answer("Are you authorized to work in the US?")
        assert not answer.needs_user_input
        assert answer.choice == "yes"
        assert answer.confidence is Confidence.HIGH

    def test_an_unrecognised_question_with_no_ai_is_unknown_not_blank_text(self, brain, posting):
        answer = QuestionAnswerer(brain, posting).answer(
            "Describe a time you disagreed with your manager."
        )
        assert answer.needs_user_input
        assert answer.text == ""

    def test_an_ai_that_declines_is_respected_rather_than_overridden(self, brain, posting):
        class DecliningClient:
            def complete(self, *, system, prompt):
                return "UNKNOWN"

        answer = QuestionAnswerer(brain, posting, ai_client=DecliningClient()).answer(
            "What was your exact GPA?"
        )
        assert answer.needs_user_input
        assert "invent" in answer.reason or "truthful" in answer.reason


class TestEveryRefusalIsActionable:
    @pytest.mark.parametrize(
        "question",
        [
            "Are you authorized to work in the US?",
            "Will you require visa sponsorship?",
            "What is your GitHub profile?",
            "Describe a time you led a team.",
        ],
    )
    def test_a_refusal_says_why_and_what_is_needed(self, brain, posting, question):
        answer = QuestionAnswerer(brain, posting).answer(question)
        assert answer.needs_user_input
        assert answer.reason, f"{question!r} was refused with no reason"
        assert answer.needs, f"{question!r} was refused with no remedy"

    def test_a_missing_phone_names_the_field_to_fill_in(self, brain, posting):
        brain.identity.phone = ""
        answer = QuestionAnswerer(brain, posting).answer("Mobile number")
        assert "phone" in answer.reason.lower()
        assert "career brain" in answer.needs.lower()


class TestConfidenceLevels:
    def test_a_profile_fact_is_high_confidence(self, brain, posting):
        answerer = QuestionAnswerer(brain, posting)
        assert answerer.answer("First name").confidence is Confidence.HIGH
        assert answerer.answer("Email").confidence is Confidence.HIGH
        assert answerer.answer("Current employer").confidence is Confidence.HIGH
        assert answerer.answer("How many years of experience?").confidence is Confidence.HIGH

    def test_generated_prose_is_medium_not_high(self, brain, posting):
        # True, grounded in the profile — and still something a human should
        # read before it reaches an employer.
        answer = QuestionAnswerer(brain, posting).answer("Why do you want to work here?")
        assert answer.confidence is Confidence.MEDIUM
        assert answer.confidence.needs_review

    def test_an_assumed_default_is_low_confidence(self, brain, posting):
        # "Immediately / 2 weeks' notice" is a reasonable default and is not
        # something the profile states anywhere.
        answerer = QuestionAnswerer(brain, posting)
        assert answerer.answer("What is your notice period?").confidence is Confidence.LOW
        assert answerer.answer("Salary expectations?").confidence is Confidence.LOW

    def test_a_stated_salary_minimum_is_a_fact_again(self, brain, posting):
        brain.preferences.min_salary = 90000
        answer = QuestionAnswerer(brain, posting).answer("Salary expectations?")
        assert answer.confidence is Confidence.HIGH
        assert "90,000" in answer.text

    def test_only_high_confidence_skips_review(self):
        assert not Confidence.HIGH.needs_review
        assert Confidence.MEDIUM.needs_review
        assert Confidence.LOW.needs_review
        assert Confidence.UNKNOWN.needs_review


class TestAnswerAll:
    def test_it_returns_both_the_answers_and_what_it_refused(self, brain, posting):
        answers, unanswered = QuestionAnswerer(brain, posting).answer_all(
            ["First name", "Are you authorized to work in the US?", "Email"]
        )
        assert answers["First name"] == "Ada"
        assert answers["Email"] == "ada@example.com"
        assert [u.question for u in unanswered] == ["Are you authorized to work in the US?"]
        assert unanswered[0].why and unanswered[0].needs

    def test_a_refused_question_never_appears_in_the_answers(self, brain, posting):
        answers, _ = QuestionAnswerer(brain, posting).answer_all(
            ["Will you require visa sponsorship?"]
        )
        assert answers == {}

    def test_the_description_carries_all_three_parts(self, brain, posting):
        _, unanswered = QuestionAnswerer(brain, posting).answer_all(
            ["Are you authorized to work in the US?"]
        )
        text = unanswered[0].describe()
        assert "authorized" in text
        assert "why:" in text and "needs:" in text


class TestApplicationMemory:
    def test_an_answer_the_user_gives_is_reused_next_time(self, brain, posting):
        question = "Do you have experience with Snowflake?"
        assert QuestionAnswerer(brain, posting).answer(question).needs_user_input

        remember_answer(brain, question, "Yes — two years at Acme.")

        # Same brain, new answerer: the question is no longer asked.
        again = QuestionAnswerer(brain, posting).answer(question)
        assert not again.needs_user_input
        assert again.text == "Yes — two years at Acme."

    def test_a_reworded_question_hits_the_same_memory(self, brain, posting):
        # Otherwise the user answers the same thing on every application.
        remember_answer(brain, "Do you have experience with Snowflake?", "Yes.")
        answer = QuestionAnswerer(brain, posting).answer("Experience with Snowflake")
        assert answer.text == "Yes."

    def test_the_memory_key_drops_filler_words(self):
        assert memory_key_for("Do you have experience with Google Ads?") == (
            "experience with google ads"
        )

    def test_an_empty_answer_is_not_remembered(self, brain):
        remember_answer(brain, "Anything?", "")
        assert brain.preferences.screening_answers == {}


class TestCommonLocationPhrasings:
    """ "Where are you currently located?" came back as NEEDS_USER_INPUT on a
    live Ashby posting purely because the rule matched "based" but not
    "located". The profile had the answer the whole time."""

    @pytest.mark.parametrize(
        "question",
        [
            "Location",
            "City",
            "Country",
            "Where are you based?",
            "Where are you currently located?",
            "What time zone are you in?",
        ],
    )
    def test_location_phrasings_are_answered_from_the_profile(self, brain, posting, question):
        brain.identity.location = "Kanpur, Uttar Pradesh, India"
        answer = QuestionAnswerer(brain, posting).answer(question)
        assert not answer.needs_user_input, question
        assert "Kanpur" in answer.text

    def test_ethnicity_still_falls_through_to_the_demographics_rule(self, brain, posting):
        # The reason the city/country patterns are word-bounded: "ethni-CITY".
        brain.identity.location = "Kanpur, Uttar Pradesh, India"
        answer = QuestionAnswerer(brain, posting).answer("Race / Ethnicity")
        assert answer.text == "Prefer not to say"
