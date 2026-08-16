"""Tests for the arbitrary-question answerer — truthful from the brain,
honest (answerable=False) when it can't know."""

from __future__ import annotations

from datetime import date

import pytest

from careeros_application_engine import QuestionAnswerer
from careeros_career_brain import CareerBrain, Experience, Identity, Preferences, Skill
from careeros_job_providers import JobPosting


@pytest.fixture
def brain():
    return CareerBrain(
        identity=Identity(
            full_name="Sahil Sachdeva",
            email="sahil@example.com",
            phone="+91 91298 32709",
            location="India (Remote)",
            headline="Performance Marketing Specialist",
            summary="4+ years scaling DTC brands.",
            links={
                "linkedin": "https://www.linkedin.com/in/sahilrit/",
                "portfolio": "https://sahilsachdevaprojects.netlify.app/",
            },
        ),
        skills=[
            Skill(name="Meta Ads", years_experience=4),
            Skill(name="Shopify", years_experience=4),
        ],
        experiences=[
            Experience(
                company_name="Presha Trading",
                title="PPC Manager",
                start_date=date(2024, 5, 1),
            )
        ],
        preferences=Preferences(min_salary=60000, salary_currency="USD"),
    )


@pytest.fixture
def answerer(brain):
    return QuestionAnswerer(brain)


def test_name_email_phone(answerer):
    assert answerer.answer("First Name").text == "Sahil"
    assert answerer.answer("Last Name").text == "Sachdeva"
    assert answerer.answer("Email").text == "sahil@example.com"
    assert answerer.answer("Phone").text == "+91 91298 32709"


def test_links(answerer):
    assert "linkedin.com/in/sahilrit" in answerer.answer("LinkedIn Profile URL").text
    assert "netlify.app" in answerer.answer("Portfolio / Website").text


def test_current_employer_and_title(answerer):
    assert answerer.answer("Who is your current or previous employer?").text == "Presha Trading"
    assert answerer.answer("What is your current or previous job title?").text == "PPC Manager"


def test_years_of_experience(answerer):
    assert answerer.answer("How many years of experience do you have?").text == "4"


def test_salary_from_preferences(answerer):
    assert "60,000" in answerer.answer("Expected salary / compensation?").text


def test_skill_screening_yes(answerer):
    a = answerer.answer("Do you have experience with Meta Ads?")
    assert a.text == "Yes"


def test_unknown_skill_screening_is_not_answered(answerer):
    a = answerer.answer("Do you have experience with Kubernetes?")
    assert a.answerable is False


def test_sponsorship_is_never_guessed(answerer):
    assert answerer.answer("Do you require visa sponsorship?").answerable is False


def test_eeo_is_declined_politely(answerer):
    a = answerer.answer("What is your gender?")
    assert a.answerable is True
    assert "prefer not" in a.text.lower()


def test_unknown_question_is_not_answered(answerer):
    assert answerer.answer("What is your favorite color?").answerable is False


def test_why_question_uses_posting_context(brain):
    posting = JobPosting(
        source_provider="test",
        external_id="1",
        title="Performance Marketing Manager",
        company_name="Acme",
        url="https://x/1",
        remote=True,
        tags=["meta ads"],
        description="Meta Ads and Shopify.",
    )
    answerer = QuestionAnswerer(brain, posting)
    a = answerer.answer("Why are you interested in this role?")
    assert a.answerable is True
    assert "Acme" in a.text


def test_missing_phone_is_not_answered():
    brain = CareerBrain(identity=Identity(full_name="No Phone", email="np@example.com"))
    assert QuestionAnswerer(brain).answer("Phone number").answerable is False
