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
