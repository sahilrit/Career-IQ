"""Tests for generate_questions."""

from __future__ import annotations

from careeros_interview_intelligence import CompanyResearch, generate_questions


def test_technical_questions_use_the_highest_proficiency_skills(brain):
    questions = generate_questions(
        brain, job_title="Backend Engineer", company_name="Widget Co", top_skills=2
    )
    assert any("Python" in q for q in questions.technical)
    assert any("Django" in q for q in questions.technical)
    assert not any("SQL" in q for q in questions.technical)  # lowest proficiency, excluded


def test_company_specific_questions_mention_the_company():
    from careeros_career_brain import CareerBrain, Identity

    brain = CareerBrain(identity=Identity(full_name="Ada", email="ada@example.com"))
    questions = generate_questions(brain, job_title="Engineer", company_name="Widget Co")
    assert all("Widget Co" in q for q in questions.company_specific)


def test_competitor_question_added_when_research_has_competitors(brain):
    research = CompanyResearch(calendar_event_id="event-1", competitors=["Acme Rival"])
    questions = generate_questions(
        brain, job_title="Engineer", company_name="Widget Co", research=research
    )
    assert any("Acme Rival" in q for q in questions.company_specific)


def test_star_prompts_are_built_from_real_achievements(brain):
    questions = generate_questions(
        brain,
        job_title="Backend Engineer",
        company_name="Widget Co",
        job_description="Own our Shopify checkout experience.",
    )
    assert len(questions.star_prompts) >= 1
    prompt = questions.star_prompts[0]
    assert "Shopify checkout" in prompt.achievement_description
    assert prompt.metric == "+18% conversion"
    assert "rebuilt the shopify checkout flow" in prompt.question.lower()


def test_role_specific_questions_are_always_present(brain):
    questions = generate_questions(brain, job_title="Engineer", company_name="Widget Co")
    assert len(questions.role_specific) >= 1
