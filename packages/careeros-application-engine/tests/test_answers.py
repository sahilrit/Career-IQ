"""Tests for templated application answers."""

from __future__ import annotations

from careeros_application_engine import (
    ANSWER_GENERATORS,
    answer_greatest_achievement,
    answer_why_this_role,
    answer_why_you,
    generate_answers,
)


def test_why_this_role_mentions_title_company_and_skills(brain, posting):
    answer = answer_why_this_role(brain, posting)
    assert "Senior Python Engineer" in answer
    assert "Widget Co" in answer
    assert "Python" in answer


def test_greatest_achievement_uses_the_top_ranked_achievement(brain, posting):
    answer = answer_greatest_achievement(brain, posting)
    assert "Rebuilt the Shopify checkout flow" in answer
    assert "+18% conversion" in answer


def test_greatest_achievement_falls_back_with_no_achievements(brain_factory, posting):
    brain = brain_factory(experiences=[])
    answer = answer_greatest_achievement(brain, posting)
    assert "measurable impact" in answer


def test_why_you_mentions_headline_and_seniority(brain, posting):
    answer = answer_why_you(brain, posting)
    assert "Backend Engineer" in answer
    assert "senior" in answer.lower()


def test_generate_answers_returns_every_registered_question(brain, posting):
    answers = generate_answers(brain, posting)
    assert set(answers.keys()) == set(ANSWER_GENERATORS.keys())
    assert all(isinstance(text, str) and text for text in answers.values())
