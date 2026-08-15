"""Tests for TemplateCoverLetterGenerator."""

from __future__ import annotations

from careeros_application_engine import TemplateCoverLetterGenerator


def test_letter_addresses_the_company_and_role(brain, posting):
    letter = TemplateCoverLetterGenerator().generate(brain, posting)
    assert "Widget Co" in letter
    assert "Senior Python Engineer" in letter


def test_letter_is_signed_with_the_users_full_name(brain, posting):
    letter = TemplateCoverLetterGenerator().generate(brain, posting)
    assert letter.strip().endswith("Ada Lovelace")


def test_letter_opening_mentions_current_role_when_present(brain, posting):
    letter = TemplateCoverLetterGenerator().generate(brain, posting)
    assert "Senior Backend Engineer at Acme" in letter


def test_letter_opening_falls_back_without_current_role(brain_factory, posting):
    brain = brain_factory(experiences=[])
    letter = TemplateCoverLetterGenerator().generate(brain, posting)
    assert "strong fit" in letter


def test_letter_body_mentions_matched_skills_and_achievement_metric(brain, posting):
    letter = TemplateCoverLetterGenerator().generate(brain, posting)
    assert "Python" in letter
    assert "+18% conversion" in letter
