"""Tests for resume content selection and rendering."""

from __future__ import annotations

from datetime import date

from careeros_application_engine import (
    build_resume_content,
    render_resume_html,
    render_resume_markdown,
    render_resume_text,
)
from careeros_career_brain import Experience


def test_build_resume_content_pulls_identity_fields(brain, posting):
    content = build_resume_content(brain, posting)
    assert content.full_name == "Ada Lovelace"
    assert content.email == "ada@example.com"
    assert content.location == "Remote"


def test_experiences_are_ordered_most_recent_first(brain_factory, posting):
    brain = brain_factory(
        experiences=[
            Experience(company_name="Old", title="Engineer", start_date=date(2015, 1, 1)),
            Experience(company_name="New", title="Engineer", start_date=date(2022, 1, 1)),
        ]
    )
    content = build_resume_content(brain, posting)
    assert [e.company_name for e in content.experiences] == ["New", "Old"]


def test_summary_mentions_matched_skills(brain, posting):
    content = build_resume_content(brain, posting)
    assert "Python" in content.summary
    assert "Django" in content.summary


def test_render_text_includes_name_skills_and_achievement_with_metric(brain, posting):
    content = build_resume_content(brain, posting)
    text = render_resume_text(content)
    assert "Ada Lovelace" in text
    assert "Python, Django" in text or "Python" in text
    assert "Rebuilt the Shopify checkout flow (+18% conversion)" in text


def test_render_markdown_uses_markdown_headers(brain, posting):
    content = build_resume_content(brain, posting)
    markdown = render_resume_markdown(content)
    assert markdown.startswith("# Ada Lovelace")
    assert "## Experience" in markdown


def test_render_html_escapes_untrusted_content(brain_factory, posting):
    from careeros_career_brain import Identity

    brain = brain_factory(
        identity=Identity(full_name="<script>alert(1)</script>", email="x@example.com")
    )
    html = render_resume_html(build_resume_content(brain, posting))
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_render_html_includes_experience_section(brain, posting):
    html = render_resume_html(build_resume_content(brain, posting))
    assert "<h2>Experience</h2>" in html
    assert "Rebuilt the Shopify checkout flow" in html
