"""Tests for research checklist and one-page briefing generation."""

from __future__ import annotations

from careeros_interview_intelligence import (
    CompanyResearch,
    generate_one_page_briefing,
    generate_research_checklist,
    render_one_page_briefing,
)


def test_checklist_is_incomplete_with_no_research():
    checklist = generate_research_checklist("Acme", None)
    assert checklist.is_complete is False
    assert checklist.completed_items == []


def test_checklist_reflects_completed_fields():
    research = CompanyResearch(
        calendar_event_id="event-1",
        business_model="B2B SaaS",
        products=["Widget"],
        competitors=["Rival Co"],
    )
    checklist = generate_research_checklist("Acme", research)
    assert "Business model" in checklist.completed_items
    assert "Products" in checklist.completed_items
    assert "Interviewer backgrounds" not in checklist.completed_items
    assert checklist.is_complete is False


def test_checklist_is_complete_when_every_field_filled():
    research = CompanyResearch(
        calendar_event_id="event-1",
        business_model="B2B SaaS",
        products=["Widget"],
        competitors=["Rival Co"],
        recent_developments=["raised Series B"],
        marketing_notes="brand-led growth",
        website_notes="clean checkout flow",
        interviewer_backgrounds={"Jane Smith": "Eng manager, ex-Google"},
    )
    checklist = generate_research_checklist("Acme", research)
    assert checklist.is_complete is True


def test_one_page_briefing_includes_strongest_achievement(brain):
    briefing = generate_one_page_briefing(
        brain,
        job_title="Backend Engineer",
        company_name="Widget Co",
        job_description="Own our Shopify checkout experience.",
    )
    assert any("Shopify checkout" in item for item in briefing.strongest_achievements)


def test_compensation_strategy_reflects_min_salary(brain):
    with_min = generate_one_page_briefing(
        brain, job_title="Engineer", company_name="Widget Co", min_salary=150_000
    )
    without_min = generate_one_page_briefing(
        brain, job_title="Engineer", company_name="Widget Co", min_salary=None
    )
    assert "150,000" in with_min.compensation_strategy
    assert "No minimum salary" in without_min.compensation_strategy


def test_things_to_avoid_warns_against_fabrication(brain):
    briefing = generate_one_page_briefing(brain, job_title="Engineer", company_name="Widget Co")
    assert any("claim experience" in item for item in briefing.things_to_avoid)


def test_render_one_page_briefing_produces_all_sections(brain):
    briefing = generate_one_page_briefing(brain, job_title="Engineer", company_name="Widget Co")
    text = render_one_page_briefing(briefing)
    assert "STRONGEST ACHIEVEMENTS TO MENTION" in text
    assert "QUESTIONS TO ASK" in text
    assert "COMPENSATION STRATEGY" in text
    assert "THINGS TO AVOID" in text
