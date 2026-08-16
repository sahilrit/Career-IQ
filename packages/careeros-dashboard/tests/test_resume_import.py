"""Tests for the heuristic resume parser and Career Brain import."""

from __future__ import annotations

import pytest

from careeros_career_brain import CareerBrainRepository
from careeros_common import DocumentStore
from careeros_dashboard.resume_import import import_resume, parse_resume

RESUME_TEXT = """SAHIL SACHDEVA
Performance Marketing Specialist | E-commerce Meta Ads CRO Shopify
sahilrit09@gmail.com | +91 91298 32709 | linkedin.com/in/sahilrit

PROFESSIONAL SUMMARY
Results-driven Performance Marketing Specialist with 4+ years scaling DTC
e-commerce brands. Generated $12M+ in revenue.

CORE COMPETENCIES
Paid Media: Meta Ads, Campaign Strategy, A/B Testing, Retargeting
E-commerce & CRO: Shopify Development, Landing Page Design, Conversion Rate Optimization

PROFESSIONAL EXPERIENCE
PPC Manager
"""


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


def test_parse_extracts_identity_fields():
    parsed = parse_resume(RESUME_TEXT)
    assert parsed.full_name == "Sahil Sachdeva"
    assert parsed.email == "sahilrit09@gmail.com"
    assert "91298" in parsed.phone
    assert "Performance Marketing" in parsed.headline


def test_parse_extracts_summary():
    parsed = parse_resume(RESUME_TEXT)
    assert "Performance Marketing Specialist" in parsed.summary
    assert "Generated $12M" in parsed.summary


def test_parse_extracts_skills_without_category_labels():
    parsed = parse_resume(RESUME_TEXT)
    assert "Meta Ads" in parsed.skills
    assert "Shopify Development" in parsed.skills
    # The "Paid Media:" category label is stripped, not kept as a skill.
    assert "Paid Media" not in parsed.skills


def _resume_pdf_bytes() -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_margins(15, 15)
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    usable_width = pdf.w - 30
    for line in RESUME_TEXT.splitlines():
        pdf.multi_cell(usable_width, 5, line or " ")
    return bytes(pdf.output())


def test_import_resume_round_trips_through_a_real_pdf(store):
    _, parsed = import_resume(store, _resume_pdf_bytes())
    assert parsed.email == "sahilrit09@gmail.com"
    loaded = CareerBrainRepository(store).list_all()[0]
    assert loaded.identity.full_name == "Sahil Sachdeva"
    assert any(s.name == "Meta Ads" for s in loaded.skills)


def test_import_resume_rejects_a_blank_pdf(store):
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    with pytest.raises(ValueError, match="Couldn't read"):
        import_resume(store, bytes(pdf.output()))
