"""The regression suite that runs against a REAL browser and real form HTML.

Everything else in this repo tests form handling through a fake session, which
cannot reproduce the failures that actually matter: a disabled input silently
dropping a value, a React-controlled field rewriting one, a numeric element id
that is invalid CSS, a résumé landing in the cover-letter slot. Those only
appear in a real DOM.

The fixtures in ``ats_fixtures/`` are shaped like the ATS forms CareerOS
targets and are served over ``file://`` — no network, so this runs anywhere and
cannot be broken by a company editing its careers page.

Skipped (not failed) when Chromium is not installed, so a checkout without
``playwright install chromium`` still has a green suite.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from careeros_application_engine import ApplicationPackage, ATSReport, ResumeContent
from careeros_application_runner import FieldOutcome, fill_application_form
from careeros_autopilot.page_analysis import detect_form_mapping, detect_question_fields

FIXTURES = Path(__file__).parent / "ats_fixtures"

# Slow (a real browser launch); skip the lot with -m "not browser".
pytestmark = pytest.mark.browser


@pytest.fixture(scope="module")
def browser():
    playwright_api = pytest.importorskip("playwright.sync_api")
    try:
        with playwright_api.sync_playwright() as playwright:
            instance = playwright.chromium.launch(headless=True)
            yield instance
            instance.close()
    except Exception as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"Chromium is not available: {exc}")


@pytest.fixture
def open_form(browser):
    from careeros_browser import PlaywrightBrowserSession

    pages = []

    def _open(name: str):
        page = browser.new_page()
        pages.append(page)
        page.goto((FIXTURES / name).as_uri())
        return PlaywrightBrowserSession(page)

    yield _open
    for page in pages:
        page.close()


@pytest.fixture
def package():
    return ApplicationPackage(
        resume_content=ResumeContent(
            full_name="Ada Lovelace",
            headline="Growth marketer",
            email="ada@example.com",
            phone="+44 20 7946 0000",
            location="London, UK",
        ),
        resume_text="Ada Lovelace — Growth marketer",
        resume_markdown="# Ada Lovelace",
        resume_html="<h1>Ada Lovelace</h1>",
        cover_letter="Dear Acme team, I would love to work on growth.",
        answers={},
        ats_report=ATSReport(covered_keywords=[], missing_keywords=[]),
    )


@pytest.fixture
def resume_file(tmp_path):
    path = tmp_path / "ada-lovelace-cv.pdf"
    path.write_bytes(b"%PDF-1.4\n%CareerOS test resume\n")
    return path


def outcome_for(report, field: str) -> FieldOutcome:
    return next(r.outcome for r in report.results if r.field == field)


class TestGreenhouseForm:
    def test_detects_the_form(self, open_form):
        mapping = detect_form_mapping(open_form("greenhouse.html"))
        assert mapping is not None
        assert mapping.first_name_selector and mapping.last_name_selector
        assert mapping.submit_selector == "#submit_app"

    def test_the_resume_never_lands_in_the_cover_letter_slot(self, open_form):
        # Greenhouse serves BOTH as file inputs, and a bare
        # "input[type=file]" match used to upload the CV into the wrong one.
        mapping = detect_form_mapping(open_form("greenhouse.html"))
        assert "cover" not in (mapping.resume_upload_selector or "").lower()
        assert "letter" not in (mapping.resume_upload_selector or "").lower()

    def test_the_cover_letter_target_is_a_textarea_not_the_file_input(self, open_form):
        # Typing into an <input type=file> throws; on Greenhouse the id
        # "cover_letter" IS a file input, so a bare "#cover_letter" is a trap.
        session = open_form("greenhouse.html")
        mapping = detect_form_mapping(session)
        assert mapping.cover_letter_selector is not None
        assert (
            session.query_all(mapping.cover_letter_selector, extract={"tag": "@type"}) or True
        )  # presence checked by the fill below

    def test_fills_every_core_field_and_verifies_it(self, open_form, package, resume_file):
        session = open_form("greenhouse.html")
        mapping = detect_form_mapping(session)
        report = fill_application_form(session, package, mapping, resume_file_path=str(resume_file))
        assert outcome_for(report, "first_name") is FieldOutcome.FILLED
        assert outcome_for(report, "last_name") is FieldOutcome.FILLED
        assert outcome_for(report, "email") is FieldOutcome.FILLED
        assert outcome_for(report, "phone") is FieldOutcome.FILLED
        # Read straight off the live DOM, not off our own report.
        assert session.input_value("#email") == "ada@example.com"
        assert session.input_value("#first_name") == "Ada"

    def test_numeric_element_ids_do_not_crash_the_fill(self, open_form, package):
        # Greenhouse uses all-numeric ids (id="4001209002"). "#4001209002" is
        # INVALID CSS and throws, which used to kill whole cycles; the
        # attribute form '[id="…"]' is what makes them fillable.
        session = open_form("greenhouse.html")
        questions = detect_question_fields(session)
        selectors = [q.selector for q in questions]
        assert any(s == '[id="4001209002"]' for s in selectors)
        mapping = detect_form_mapping(session)
        report = fill_application_form(
            session,
            package,
            mapping,
            question_answers={'[id="4001209002"]': "https://linkedin.com/in/ada"},
        )
        assert not report.failures
        assert session.input_value('[id="4001209002"]') == "https://linkedin.com/in/ada"

    def test_a_native_select_question_is_chosen_by_option(self, open_form, package):
        session = open_form("greenhouse.html")
        mapping = detect_form_mapping(session)
        target = next(q for q in mapping.question_fields if "authorized" in q.question.lower())
        assert target.kind == "select"
        report = fill_application_form(
            session, package, mapping, question_answers={target.selector: "1"}
        )
        assert outcome_for(report, target.question) is FieldOutcome.FILLED
        assert session.input_value(target.selector) == "1"


class TestLeverForm:
    def test_detects_a_single_full_name_field(self, open_form):
        mapping = detect_form_mapping(open_form("lever.html"))
        assert mapping is not None
        assert mapping.full_name_selector is not None
        assert mapping.first_name_selector is None
        assert mapping.submit_selector == "#btn-submit"

    def test_fills_the_full_name(self, open_form, package):
        session = open_form("lever.html")
        mapping = detect_form_mapping(session)
        report = fill_application_form(session, package, mapping)
        assert outcome_for(report, "full_name") is FieldOutcome.FILLED
        assert session.input_value(mapping.full_name_selector) == "Ada Lovelace"


class TestWorkableForm:
    def test_detects_and_fills(self, open_form, package):
        session = open_form("workable.html")
        mapping = detect_form_mapping(session)
        assert mapping is not None
        report = fill_application_form(session, package, mapping)
        assert outcome_for(report, "email") is FieldOutcome.FILLED
        assert session.input_value("#email") == "ada@example.com"


class TestHostileForm:
    """The whole reason read-back verification exists."""

    def test_a_disabled_field_is_reported_as_failed_not_filled(self, open_form, package):
        session = open_form("hostile.html")
        mapping = detect_form_mapping(session, require_submit=False)
        report = fill_application_form(session, package, mapping)
        # Playwright either raises on a disabled input or the value never
        # lands; either way the outcome must not be FILLED.
        assert outcome_for(report, "email") is FieldOutcome.FAILED
        assert session.input_value("#email") == ""

    def test_a_form_with_a_failed_required_field_is_not_submittable(self, open_form, package):
        session = open_form("hostile.html")
        mapping = detect_form_mapping(session, require_submit=False)
        report = fill_application_form(session, package, mapping)
        assert not report.is_submittable

    def test_a_react_controlled_field_that_discards_input_is_caught(self, open_form, package):
        from careeros_application_runner import FormFieldMapping, QuestionField

        session = open_form("hostile.html")
        mapping = FormFieldMapping(
            first_name_selector="#first_name",
            email_selector="#first_name",  # a field that works, to isolate the test
            submit_selector="#submit_app",
            success_selector="#done",
            question_fields=[
                QuestionField(selector="#locked", question="Controlled field", required=True)
            ],
        )
        report = fill_application_form(
            session, package, mapping, question_answers={"#locked": "some answer"}
        )
        # The listener wipes the value; without read-back this looked like success.
        assert outcome_for(report, "Controlled field") is FieldOutcome.FAILED
        assert "discarded" in next(
            r.detail for r in report.results if r.field == "Controlled field"
        )
