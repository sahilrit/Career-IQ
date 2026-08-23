"""Best-effort experience extraction from résumé text."""

from __future__ import annotations

from careeros_career_brain import parse_resume


def test_extracts_experiences_anchored_on_dates():
    txt = (
        "EXPERIENCE\n"
        "Senior Marketer \u2014 Acme    Jan 2021 - Present\n"
        "Growth Lead, BetaCorp   Mar 2019 \u2013 Dec 2020\n"
        "EDUCATION\n"
        "B.Tech 2015 - 2019\n"
    )
    exps = parse_resume(txt).experiences
    assert [(e.title, e.company) for e in exps] == [
        ("Senior Marketer", "Acme"),
        ("Growth Lead", "BetaCorp"),
    ]
    assert exps[0].end_date is None  # "Present"
    assert exps[0].start_date.year == 2021
    assert exps[1].start_date.year == 2019 and exps[1].end_date.year == 2020


def test_no_experience_section_is_empty():
    assert parse_resume("SKILLS\nMeta Ads, SQL, CRO").experiences == []


def test_lines_without_dates_are_ignored():
    # A responsibilities bullet with no date must not become a fake role.
    txt = "EXPERIENCE\nMarketing Manager at Acme  2020 - 2022\n- Did great things\nEDUCATION\n"
    exps = parse_resume(txt).experiences
    assert len(exps) == 1 and exps[0].title == "Marketing Manager"


def test_title_above_company_pipe_dates_location_format():
    # The common modern layout: title on its own line, then
    # "Company | Dates | Location" — and a prose note must be ignored.
    txt = (
        "PROFESSIONAL EXPERIENCE\n"
        "Independent Performance Marketing Consultant\n"
        "Self-Employed | May 2025 \u2013 Present | Remote\n"
        "\x7f Generated $2.4M in revenue at 6-8x ROAS.\n"
        "PPC Manager\n"
        "Presha Trading | May 2024 \u2013 May 2025 | Delhi\n"
        "\x7f Increased order volume by 650%.\n"
        "Concurrent with full-time role at PerformUP ( ); transitioned 2022 \u2013 2023\n"
        "EDUCATION\n"
    )
    exps = parse_resume(txt).experiences
    assert [(e.title, e.company) for e in exps] == [
        ("Independent Performance Marketing Consultant", "Self-Employed"),
        ("PPC Manager", "Presha Trading"),
    ]
    assert exps[0].end_date is None  # Present
    assert exps[1].start_date.year == 2024 and exps[1].end_date.year == 2025


def test_experience_captures_bullet_description():
    txt = (
        "PROFESSIONAL EXPERIENCE\n"
        "PPC Manager\n"
        "Acme | Jan 2021 - Present | Remote\n"
        "\x7f Grew revenue 30%.\n"
        "\x7f Cut CPA by 20%.\n"
        "EDUCATION\n"
    )
    exp = parse_resume(txt).experiences[0]
    assert "Grew revenue 30%." in exp.description
    assert "Cut CPA by 20%." in exp.description


def test_extracts_education_credential_and_institution():
    txt = (
        "EDUCATION\nBachelor of Computer Applications (BCA)\nAxis College | 2023\nCERTIFICATIONS\n"
    )
    edu = parse_resume(txt).education
    assert len(edu) == 1
    assert edu[0].credential == "Bachelor of Computer Applications (BCA)"
    assert edu[0].institution == "Axis College"
    assert edu[0].end_date.year == 2023


def test_extracts_certifications_name_and_issuer():
    txt = "CERTIFICATIONS\n\x7f Digital Marketing \u2014 HubSpot Academy\n\x7f SEO \u2014 Google\n"
    certs = parse_resume(txt).certifications
    assert (certs[0].name, certs[0].issuer) == ("Digital Marketing", "HubSpot Academy")
    assert (certs[1].name, certs[1].issuer) == ("SEO", "Google")
