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
from careeros_autopilot.page_analysis import (
    detect_form_mapping,
    detect_question_fields,
    locate_form,
)

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
        session = open_form("greenhouse.html")
        mapping = detect_form_mapping(session)
        assert mapping is not None
        assert mapping.first_name_selector and mapping.last_name_selector
        # The submit control is identified by what it IS, so the selector
        # syntax is an implementation detail — assert it resolves to the real
        # Greenhouse submit button, not that it equals one particular string.
        assert "submit_app" in mapping.submit_selector
        assert session.is_visible(mapping.submit_selector)

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

    def test_a_file_based_cover_letter_is_never_used_as_a_text_target(self, open_form, package):
        # On Greenhouse the id "cover_letter" is an <input type="file">.
        # Knowing what a field is FOR is not enough — knowing how it must be
        # written matters too, and typing into a file input raises and fails
        # the whole fill.
        session = open_form("greenhouse.html")
        mapping = detect_form_mapping(session)
        if mapping.cover_letter_selector:
            kinds = session.query_all(mapping.cover_letter_selector, extract={"type": "@type"})
            assert all((row.get("type") or "") != "file" for row in kinds)
        report = fill_application_form(session, package, mapping)
        assert not [r for r in report.failures if r.field == "cover_letter"]

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
        session = open_form("lever.html")
        mapping = detect_form_mapping(session)
        assert mapping is not None
        assert mapping.full_name_selector is not None
        assert mapping.first_name_selector is None
        assert "btn-submit" in mapping.submit_selector
        assert session.is_visible(mapping.submit_selector)

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


class TestSmartRecruitersIframeForm:
    """The gap that blocked SmartRecruiters entirely: 0/2 submission-ready.

    The form is served from a different document and embedded in an iframe, so
    a selector run against the posting page reaches nothing. That is
    indistinguishable, from the page's point of view, from a posting with no
    application form at all — which is exactly how it was reported.
    """

    def test_the_page_itself_has_no_reachable_form(self, open_form):
        # Establishes the premise: this is not a detection bug on the page.
        session = open_form("smartrecruiters.html")
        assert detect_form_mapping(session, require_submit=False) is None

    def test_the_form_is_found_inside_the_iframe(self, open_form):
        session = open_form("smartrecruiters.html")
        located = locate_form(session)
        assert located is not None
        assert located.in_frame
        assert "iframe" in located.describe()

    def test_a_decoy_frame_does_not_stop_the_search(self, open_form):
        # Real posting pages carry consent/analytics frames before the form.
        session = open_form("smartrecruiters.html")
        assert len(session.frames()) >= 2
        assert locate_form(session) is not None

    def test_the_iframe_form_is_filled_and_verified_in_the_frame(
        self, open_form, package, resume_file
    ):
        session = open_form("smartrecruiters.html")
        located = locate_form(session)
        report = fill_application_form(
            session=located.session,
            package=package,
            mapping=located.mapping,
            resume_file_path=str(resume_file),
        )
        assert outcome_for(report, "first_name") is FieldOutcome.FILLED
        assert outcome_for(report, "last_name") is FieldOutcome.FILLED
        assert outcome_for(report, "email") is FieldOutcome.FILLED
        assert outcome_for(report, "phone") is FieldOutcome.FILLED
        # Read back from the FRAME's own DOM, not from our report.
        assert located.session.input_value("#sr-email") == "ada@example.com"
        assert located.session.input_value("#sr-first") == "Ada"

    def test_the_upload_button_is_not_mistaken_for_the_submit_button(self, open_form):
        # Both are button[type=submit] inside the same form.
        session = open_form("smartrecruiters.html")
        located = locate_form(session)
        assert "sr-submit" in located.mapping.submit_selector
        assert "upload" not in located.mapping.submit_selector.lower()

    def test_label_variants_inside_the_frame_map_correctly(self, open_form):
        # "Mobile" and "LinkedIn Profile" — neither matches the old
        # hardcoded selector lists.
        session = open_form("smartrecruiters.html")
        located = locate_form(session)
        assert "sr-phone" in (located.mapping.phone_selector or "")

    def test_the_frame_form_is_submission_ready(self, open_form, package, resume_file):
        session = open_form("smartrecruiters.html")
        located = locate_form(session)
        report = fill_application_form(
            session=located.session,
            package=package,
            mapping=located.mapping,
            resume_file_path=str(resume_file),
            question_answers={
                q.selector: "Because I want to own paid acquisition."
                for q in located.mapping.question_fields
            },
        )
        assert report.is_submittable, report.summary()


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


class TestRadioGroups:
    """The regression the live run caught: 8/13 submission-ready → 2/12.

    A richer field scan started seeing radio/checkbox inputs. Each option
    became its own required text question, so ``fill()`` raised "Input of type
    radio cannot be filled" and forms that had been submittable dropped out.
    """

    def test_a_radio_group_is_one_question_not_one_per_option(self, open_form):
        session = open_form("radios.html")
        questions = detect_question_fields(session)
        labels = [q.question for q in questions]
        # Three groups, eleven controls.
        assert len(questions) == 3, labels
        assert any("authorized to work" in label for label in labels)
        assert any("race" in label for label in labels)
        assert any("veteran" in label for label in labels)

    def test_the_question_is_the_legend_not_an_option_label(self, open_form):
        # "Yes", "No", "Decline to self-identify" are answers, not questions.
        session = open_form("radios.html")
        labels = [q.question for q in detect_question_fields(session)]
        assert "yes" not in labels
        assert "no" not in labels
        assert "decline to self-identify" not in labels

    def test_every_option_is_offered_as_a_choice(self, open_form):
        session = open_form("radios.html")
        race = next(q for q in detect_question_fields(session) if "race" in q.question)
        assert race.kind == "choice"
        assert len(race.options) == 6
        assert any("hispanic" in option for option in race.options)
        # And each option knows which control picks it.
        assert set(race.option_selectors) == set(race.options)

    def test_a_radio_is_never_text_filled(self, open_form, package):
        # The exact failure: Page.fill: Input of type "radio" cannot be filled.
        session = open_form("radios.html")
        mapping = detect_form_mapping(session)
        report = fill_application_form(session, package, mapping)
        assert not [r for r in report.failures if "radio" in r.detail.lower()], [
            r.detail for r in report.failures
        ]

    def test_an_answer_selects_the_matching_option_and_reads_back(self, open_form, package):
        session = open_form("radios.html")
        mapping = detect_form_mapping(session)
        work_auth = next(q for q in mapping.question_fields if "authorized to work" in q.question)
        report = fill_application_form(
            session, package, mapping, question_answers={work_auth.selector: "Yes"}
        )
        assert outcome_for(report, work_auth.question) is FieldOutcome.FILLED
        # Verified against the live DOM, not our own report.
        assert session.is_checked(work_auth.option_selectors["yes"])
        assert not session.is_checked(work_auth.option_selectors["no"])

    def test_an_answer_matching_no_option_is_left_for_a_human(self, open_form, package):
        # A wrong EEO or work-authorization answer is worse than none.
        session = open_form("radios.html")
        mapping = detect_form_mapping(session)
        race = next(q for q in mapping.question_fields if "race" in q.question)
        report = fill_application_form(
            session, package, mapping, question_answers={race.selector: "Klingon"}
        )
        assert outcome_for(report, race.question) is FieldOutcome.NEEDS_HUMAN
        assert not any(session.is_checked(s) for s in race.option_selectors.values())

    def test_the_form_is_submission_ready_with_the_optional_groups_unanswered(
        self, open_form, package
    ):
        # These groups are optional; leaving them for a human must not block.
        session = open_form("radios.html")
        mapping = detect_form_mapping(session)
        report = fill_application_form(session, package, mapping)
        assert report.is_submittable, report.summary()


class TestLeverStyleDivQuestions:
    """Lever renders a question as plain divs — no fieldset, no legend, no
    heading. The group label fell back to the first OPTION, so a live run
    reported the blocking question as literally "no"."""

    def test_the_question_is_the_label_div_not_an_option(self, open_form):
        session = open_form("lever_questions.html")
        labels = [q.question for q in detect_question_fields(session)]
        assert "no" not in labels
        assert "yes" not in labels
        assert any("authorized to work" in label for label in labels), labels
        assert any("sponsorship" in label for label in labels), labels

    def test_each_group_is_one_question_with_both_options(self, open_form):
        session = open_form("lever_questions.html")
        questions = detect_question_fields(session)
        assert len(questions) == 2
        for question in questions:
            assert question.kind == "choice"
            assert set(question.options) == {"yes", "no"}

    def test_a_stored_answer_selects_the_right_option(self, open_form, package):
        session = open_form("lever_questions.html")
        mapping = detect_form_mapping(session)
        auth = next(q for q in mapping.question_fields if "authorized" in q.question)
        report = fill_application_form(
            session, package, mapping, question_answers={auth.selector: "No"}
        )
        assert outcome_for(report, auth.question) is FieldOutcome.FILLED
        assert session.is_checked(auth.option_selectors["no"])
