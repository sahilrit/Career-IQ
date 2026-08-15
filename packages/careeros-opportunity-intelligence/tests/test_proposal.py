"""Tests for TemplateProposalGenerator."""

from __future__ import annotations

from datetime import date

from careeros_career_brain import Achievement, Experience, Skill
from careeros_freelance_providers import GigPosting
from careeros_opportunity_intelligence import TemplateProposalGenerator


def _posting(**overrides) -> GigPosting:
    defaults = {
        "source_provider": "fiverr",
        "external_id": "1",
        "title": "Shopify Storefront Redesign",
        "client_name": "ada_dev",
        "url": "https://example.com/1",
        "skills_required": ["shopify", "cro"],
        "description": "Redesign our Shopify checkout flow for better conversion.",
    }
    defaults.update(overrides)
    return GigPosting(**defaults)


def test_proposal_mentions_the_gig_title_and_full_name(brain_factory):
    brain = brain_factory()
    proposal = TemplateProposalGenerator().generate(brain, _posting())
    assert "Shopify Storefront Redesign" in proposal
    assert proposal.strip().endswith("Ada Lovelace")


def test_proposal_mentions_matched_skills(brain_factory):
    brain = brain_factory(skills=[Skill(name="Shopify", proficiency=5)])
    proposal = TemplateProposalGenerator().generate(brain, _posting())
    assert "Shopify" in proposal


def test_proposal_falls_back_without_matched_skills(brain_factory):
    brain = brain_factory(skills=[])
    proposal = TemplateProposalGenerator().generate(brain, _posting())
    assert "bring this project to life" in proposal


def test_proposal_features_a_relevant_achievement_with_its_metric(brain_factory):
    brain = brain_factory(
        experiences=[
            Experience(
                company_name="Acme",
                title="Freelance Developer",
                start_date=date(2020, 1, 1),
                achievements=[
                    Achievement(
                        description="Rebuilt a Shopify checkout flow", metric="+20% conversion"
                    )
                ],
            )
        ]
    )
    proposal = TemplateProposalGenerator().generate(brain, _posting())
    assert "Rebuilt a Shopify checkout flow" in proposal
    assert "+20% conversion" in proposal


def test_proposal_falls_back_without_any_achievements(brain_factory):
    brain = brain_factory(experiences=[])
    proposal = TemplateProposalGenerator().generate(brain, _posting())
    assert "measurable results" in proposal
