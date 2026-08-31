"""Tests for live-page form detection and apply-link discovery."""

from __future__ import annotations

from careeros_autopilot import detect_form_mapping, find_apply_url, prepare_application_page
from careeros_autopilot.page_analysis import (
    DEFAULT_PROBLEM_DETECTORS,
    ats_apply_url,
    detect_question_fields,
)
from careeros_browser import FakeBrowserSession
from careeros_human_in_the_loop import run_detectors
from careeros_job_providers import JobPosting


def make_posting(url="https://example.com/jobs/1") -> JobPosting:
    return JobPosting(
        source_provider="test",
        external_id="1",
        title="Performance Marketing Manager",
        company_name="Acme",
        url=url,
        remote=True,
    )


def test_no_form_and_no_apply_link_returns_reason():
    session = FakeBrowserSession()
    reason = prepare_application_page(session, make_posting())
    assert reason is not None
    assert "no application form" in reason


def test_ats_link_is_preferred_and_navigated_to():
    session = FakeBrowserSession()
    session.set_query_all_results(
        "a",
        [
            {"href": "https://example.com/about"},
            {"href": "https://boards.greenhouse.io/acme/jobs/123"},
        ],
    )
    assert find_apply_url(session) == "https://boards.greenhouse.io/acme/jobs/123"
    assert prepare_application_page(session, make_posting()) is None
    assert session.current_url == "https://boards.greenhouse.io/acme/jobs/123"


def test_generic_apply_suffix_link_is_found():
    session = FakeBrowserSession()
    session.set_query_all_results("a", [{"href": "https://example.com/jobs/1/apply?src=x"}])
    assert find_apply_url(session) == "https://example.com/jobs/1/apply?src=x"


def test_page_that_is_already_a_form_needs_no_navigation():
    session = FakeBrowserSession()
    session.set_visible("input[type='email']")
    session.set_visible("button[type='submit']")
    assert prepare_application_page(session, make_posting()) is None


def test_detect_form_mapping_requires_email_and_submit():
    session = FakeBrowserSession()
    assert detect_form_mapping(session) is None
    session.set_visible("input[type='email']")
    assert detect_form_mapping(session) is None
    session.set_visible("button[type='submit']")
    assert detect_form_mapping(session) is not None


def test_lenient_mapping_accepts_a_fillable_form_without_a_submit_button():
    """Prepare-and-review only needs somewhere to put the data; the human
    submits, so a visible email field is enough even with no submit button."""
    session = FakeBrowserSession()
    session.set_visible("input[type='email']")
    assert detect_form_mapping(session) is None  # strict still requires submit
    mapping = detect_form_mapping(session, require_submit=False)
    assert mapping is not None
    assert mapping.email_selector == "input[type='email']"


def test_detect_form_mapping_prefers_split_name_fields():
    session = FakeBrowserSession()
    session.set_visible("input[type='email']")
    session.set_visible("button[type='submit']")
    session.set_visible("#first_name")
    session.set_visible("#last_name")
    session.set_visible("input[autocomplete='name']")
    mapping = detect_form_mapping(session)
    assert mapping.first_name_selector == "#first_name"
    assert mapping.last_name_selector == "#last_name"
    assert mapping.full_name_selector is None


def test_detect_form_mapping_picks_up_optional_fields():
    session = FakeBrowserSession()
    for selector in (
        "input[type='email']",
        "button[type='submit']",
        "input[type='tel']",
        "input[type='file'][name*='resume' i]",
        "textarea[name*='cover' i]",
    ):
        session.set_visible(selector)
    mapping = detect_form_mapping(session)
    assert mapping.phone_selector == "input[type='tel']"
    assert mapping.resume_upload_selector == "input[type='file'][name*='resume' i]"
    assert mapping.cover_letter_selector == "textarea[name*='cover' i]"


def test_file_input_is_never_mapped_as_the_text_cover_letter():
    """Regression: on Greenhouse '#cover_letter' is an <input type=file>. The
    cover-letter TEXT field must only match a textarea, so a lone file input is
    mapped as the résumé upload, not force-typed into as a cover letter."""
    session = FakeBrowserSession()
    for selector in (
        "input[type='email']",
        "button[type='submit']",
        "input[type='file'][name*='resume' i]",
    ):
        session.set_visible(selector)
    mapping = detect_form_mapping(session)
    assert mapping is not None
    assert mapping.resume_upload_selector == "input[type='file'][name*='resume' i]"
    assert mapping.cover_letter_selector is None


def test_resume_is_never_uploaded_into_a_cover_letter_file_field():
    """Regression: a plain input[type=file] match was putting the résumé in the
    cover-letter upload slot. If only a cover-letter file input exists, the
    résumé upload must resolve to nothing rather than the wrong field."""
    session = FakeBrowserSession()
    session.set_visible("input[type='email']")
    session.set_visible("button[type='submit']")
    session.set_visible("input[type='file'][id*='cover_letter' i]")  # cover-letter upload only
    mapping = detect_form_mapping(session)
    assert mapping is not None
    assert mapping.resume_upload_selector is None


def test_invisible_recaptcha_v3_badge_does_not_trigger_a_captcha():
    """reCAPTCHA v3 keeps a visible badge (a generic 'recaptcha' iframe) with
    nothing to solve — it must NOT pause the run."""
    session = FakeBrowserSession()
    session.set_visible("iframe[src*='recaptcha']")  # the v3 badge, no challenge
    session.set_visible(".g-recaptcha")
    assert run_detectors(session, DEFAULT_PROBLEM_DETECTORS) is None


def test_visible_recaptcha_v2_checkbox_is_detected_as_a_captcha():
    session = FakeBrowserSession()
    session.set_visible("iframe[src*='api2/anchor']")  # the "I'm not a robot" checkbox
    problem = run_detectors(session, DEFAULT_PROBLEM_DETECTORS)
    assert problem is not None
    assert problem.kind == "captcha"


def test_ats_apply_url_derivation():
    assert (
        ats_apply_url("https://jobs.ashbyhq.com/openai/123")
        == "https://jobs.ashbyhq.com/openai/123/application"
    )
    assert (
        ats_apply_url("https://jobs.lever.co/spotify/abc")
        == "https://jobs.lever.co/spotify/abc/apply"
    )
    # Lever's EU subdomain (seen live via WorkingNomads) must also derive /apply.
    assert (
        ats_apply_url("https://jobs.eu.lever.co/creatio/052b5080")
        == "https://jobs.eu.lever.co/creatio/052b5080/apply"
    )
    # Greenhouse is inline; already-suffixed URLs are left alone; unknown -> None.
    assert ats_apply_url("https://boards.greenhouse.io/acme/jobs/1") is None
    assert ats_apply_url("https://jobs.ashbyhq.com/openai/123/application") is None
    assert ats_apply_url("https://example.com/jobs/1") is None


def test_prepare_navigates_to_derived_ashby_apply_form():
    """An Ashby posting page has no crawlable apply <a>; derive …/application."""
    session = FakeBrowserSession()
    posting = make_posting(url="https://jobs.ashbyhq.com/openai/123")
    assert prepare_application_page(session, posting) is None
    assert session.current_url == "https://jobs.ashbyhq.com/openai/123/application"


def test_direct_apply_url_is_used_instead_of_the_listing_page():
    """When a provider supplies apply_url (RemoteOK/WorkingNomads), go straight
    to the employer's form, not the aggregator listing at posting.url."""
    session = FakeBrowserSession()
    session.set_visible("input[type='email']")
    session.set_visible("button[type='submit']")
    posting = make_posting(url="https://www.workingnomads.com/jobs/marketing-associate").model_copy(
        update={"apply_url": "https://reflexmediainc.applytojob.com/apply/uTEp2lGf4Y"}
    )
    assert prepare_application_page(session, posting) is None
    assert session.current_url == "https://reflexmediainc.applytojob.com/apply/uTEp2lGf4Y"


def test_ashby_rendered_form_is_detected_inline_without_navigating():
    """After the SPA settles, the Ashby form fields are present on the page, so
    it's used in place — no bogus 'no form found'."""
    session = FakeBrowserSession()
    session.set_visible("input[type='email']")
    session.set_visible("button[type='submit']")
    posting = make_posting(url="https://jobs.ashbyhq.com/openai/123")
    assert prepare_application_page(session, posting) is None
    assert session.current_url == "https://jobs.ashbyhq.com/openai/123"


def test_application_suffix_link_is_found():
    session = FakeBrowserSession()
    session.set_query_all_results("a", [{"href": "https://jobs.ashbyhq.com/acme/1/application"}])
    assert find_apply_url(session) == "https://jobs.ashbyhq.com/acme/1/application"


def test_eu_lever_and_applytojob_are_recognized_as_ats_hosts():
    """Live WorkingNomads apply_urls use jobs.eu.lever.co and *.applytojob.com."""
    for href in (
        "https://jobs.eu.lever.co/creatio/052b5080",
        "https://marketmymarket.applytojob.com/apply/WjEliaC30w/PPC-Specialist",
    ):
        session = FakeBrowserSession()
        session.set_query_all_results("a", [{"href": href}])
        assert find_apply_url(session) == href


def test_bot_protection_challenge_is_reported_not_bypassed():
    from careeros_autopilot.page_analysis import _BOT_PROTECTION_SELECTORS

    session = FakeBrowserSession()
    # Drive it off the real list rather than a hardcoded copy: the literal
    # string drifted once already when Cloudflare changed its wording, and a
    # test pinned to the old copy passes while production misses the wall.
    session.set_visible(_BOT_PROTECTION_SELECTORS[0])
    session.set_query_all_results("a", [{"href": "https://example.com/jobs/1/apply"}])
    reason = prepare_application_page(session, make_posting())
    assert reason is not None
    assert "bot-protection" in reason


def test_detect_question_fields_from_labels():
    session = FakeBrowserSession()
    session.set_query_all_results(
        "textarea",
        [{"id": "q_why", "label": "Why do you want to work here?", "placeholder": None}],
    )
    session.set_query_all_results(
        "input[type='text']",
        [
            {"id": "q_emp", "label": "Current employer", "placeholder": None},
            {"id": "first_name", "label": "First Name", "placeholder": None},
        ],
    )
    fields = detect_question_fields(session)
    questions = {f.question for f in fields}
    assert "Why do you want to work here?" in questions
    assert "Current employer" in questions
    # Standard name/email/phone fields are excluded from questions.
    assert "First Name" not in questions


def test_detect_question_fields_uses_label_elements_and_selects():
    """Real forms label fields with <label for=id> and use <select> dropdowns —
    both must be detected, not just aria-label text inputs."""
    session = FakeBrowserSession()
    session.set_query_all_results(
        "label",
        [
            {"for": "q_auth", "text": "Are you authorized to work in the US?"},
            {"for": "q_src", "text": "How did you hear about us?"},
        ],
    )
    session.set_query_all_results(
        "input[type='text']",
        [{"id": "q_auth", "label": None, "placeholder": None}],
    )
    session.set_query_all_results(
        "select",
        [{"id": "q_src", "label": None, "placeholder": None}],
    )
    fields = {f.selector: f for f in detect_question_fields(session)}
    assert fields['[id="q_auth"]'].question == "Are you authorized to work in the US?"
    assert fields['[id="q_auth"]'].kind == "text"
    assert fields['[id="q_src"]'].question == "How did you hear about us?"
    assert fields['[id="q_src"]'].kind == "select"


def test_detect_question_fields_includes_custom_dropdowns():
    """React/ARIA 'Select…' dropdowns aren't native <select>; they surface via
    detect_comboboxes() and must be detected as kind='combobox'."""
    session = FakeBrowserSession()
    session.set_comboboxes(
        [
            {"selector": '[id="react-select-3-input"]', "question": "Do you require sponsorship?"},
            {"selector": '[id="cos-combo-0"]', "question": "Which state do you reside in?"},
        ]
    )
    fields = {f.selector: f for f in detect_question_fields(session)}
    assert fields['[id="react-select-3-input"]'].kind == "combobox"
    assert fields['[id="react-select-3-input"]'].question == "Do you require sponsorship?"
    assert fields['[id="cos-combo-0"]'].kind == "combobox"


def test_a_react_select_dropdown_is_classified_as_combobox_not_text():
    """Regression: a real react-select dropdown's focusable input element has
    type='text' and a real aria-label as implementation details — so it also
    matches the plain `input[type='text']` scan, WITH a usable question
    label, which is enough to enter `seen` and block the correct combobox
    classification. On a live Greenhouse form (verified 2026-08-26) this
    caused every EEO/sponsorship dropdown question ('Do you require
    immigration sponsorship...', gender, veteran status, ...) to be
    misclassified as kind='text', so fill_application_form later called a
    plain .fill() on a closed dropdown — which types into it without ever
    selecting an option, i.e. silently does nothing useful.
    detect_comboboxes() must win a selector collision, not lose to
    whichever generic scan happens to run first."""
    session = FakeBrowserSession()
    session.set_query_all_results(
        "input[type='text']",
        [
            {
                "id": "question_31786595003",
                "label": "Do you require immigration sponsorship to work in the United States?",
                "placeholder": None,
            }
        ],
    )
    session.set_comboboxes(
        [
            {
                "selector": '[id="question_31786595003"]',
                "question": "Do you require immigration sponsorship to work in the United States?",
            }
        ]
    )
    fields = [
        f for f in detect_question_fields(session) if f.selector == '[id="question_31786595003"]'
    ]
    assert len(fields) == 1
    assert fields[0].kind == "combobox"


def test_combobox_selector_already_seen_is_not_duplicated():
    """A dropdown whose selector was already reported by detect_comboboxes()
    is not added a second time by the generic scan."""
    session = FakeBrowserSession()
    session.set_comboboxes([{"selector": '[id="q_country"]', "question": "Country"}])
    session.set_query_all_results(
        "select",
        [{"id": "q_country", "label": "Country", "placeholder": None}],
    )
    fields = [f for f in detect_question_fields(session) if f.selector == '[id="q_country"]']
    assert len(fields) == 1
    assert fields[0].kind == "combobox"  # detect_comboboxes wins, seen first


def test_numeric_field_ids_produce_valid_selectors():
    """Regression: an all-numeric id like 4001209002 makes '#4001209002' an
    INVALID CSS selector that throws on fill and crashed whole cycles. Use an
    attribute selector instead."""
    session = FakeBrowserSession()
    session.set_query_all_results(
        "input[type='text']",
        [{"id": "4001209002", "label": "Years of experience", "placeholder": None}],
    )
    fields = detect_question_fields(session)
    assert fields[0].selector == '[id="4001209002"]'


class TestFindApplyUrl:
    """The extract-spec bug that made apply-link discovery a no-op everywhere."""

    def test_finds_an_ats_hosted_apply_link(self):
        from careeros_browser import FakeBrowserSession

        session = FakeBrowserSession()
        # "@href" reads the attribute off the matched <a>. The old spec was
        # "a@href", which looks for a nested <a> INSIDE each <a> — never
        # present — so this returned None on every page ever visited.
        session.set_query_all_results(
            "a",
            [
                {"href": "https://example.com/about"},
                {"href": "https://jobs.lever.co/acme/123/apply"},
            ],
        )
        assert find_apply_url(session) == "https://jobs.lever.co/acme/123/apply"

    def test_finds_a_smartrecruiters_oneclick_link(self):
        from careeros_browser import FakeBrowserSession

        session = FakeBrowserSession()
        # The link text is localised ("Jetzt bewerben"), so only the href is
        # usable for identification.
        session.set_query_all_results(
            "a",
            [{"href": "https://jobs.smartrecruiters.com/oneclick-ui/company/Acme/publication/x"}],
        )
        assert "oneclick-ui" in (find_apply_url(session) or "")

    def test_falls_back_to_a_path_ending_in_apply(self):
        from careeros_browser import FakeBrowserSession

        session = FakeBrowserSession()
        session.set_query_all_results("a", [{"href": "https://careers.acme.com/jobs/7/apply"}])
        assert find_apply_url(session) == "https://careers.acme.com/jobs/7/apply"

    def test_returns_none_when_there_is_no_apply_link(self):
        from careeros_browser import FakeBrowserSession

        session = FakeBrowserSession()
        session.set_query_all_results("a", [{"href": "https://example.com/about"}])
        assert find_apply_url(session) is None


class TestAntiBotIsNamedRatherThanMistakenForAMissingForm:
    """SmartRecruiters' oneclick-ui apply pages serve a DataDome challenge and
    NO form (observed live, 2026-08-31).

    Reported as "no fillable form found on the page or in any frame", that
    sends the user hunting for a CareerOS bug. The form is not missing — it is
    behind an anti-bot wall, and CareerOS must not try to get around one.
    """

    def test_a_datadome_challenge_is_detected_as_a_captcha(self):
        from careeros_autopilot import CAPTCHA_DETECTORS

        session = FakeBrowserSession()
        session.set_visible("iframe[src*='captcha-delivery.com']")
        found = [d.detect(session) for d in CAPTCHA_DETECTORS]
        problems = [p for p in found if p is not None]
        assert problems, "a DataDome challenge was not recognised"
        assert problems[0].kind == "captcha"
        assert "captcha" in problems[0].description

    def test_a_clean_page_trips_no_captcha_detector(self):
        from careeros_autopilot import CAPTCHA_DETECTORS

        session = FakeBrowserSession()
        session.set_visible("#email")
        assert all(d.detect(session) is None for d in CAPTCHA_DETECTORS)


class TestOneQuestionIsAskedOnce:
    """Observed live on Greenhouse (2026-08-31): "How did you hear about this
    job?" was answered TWICE — once by opening its react-select dropdown, and
    once by typing into the inner input, which silently discarded the value and
    reported a failure on a question that had already been answered correctly.

    The two scans reach the same widget through different elements, so they
    produce different selectors for it. Deduping on selector alone cannot see
    that; deduping on the question can.
    """

    def _session_with_a_react_select(self):
        session = FakeBrowserSession()
        session.set_comboboxes(
            [{"selector": '[id="combo-1"]', "question": "How did you hear about this job?"}]
        )
        # The SAME widget, reached through its inner text input.
        session.set_fields(
            [
                {
                    "selector": '[id="inner-input-1"]',
                    "type": "text",
                    "label": "How did you hear about this job?",
                },
                {"selector": '[id="q2"]', "type": "text", "label": "Why this company?"},
            ]
        )
        return session

    def test_the_same_question_is_not_asked_twice(self):
        from careeros_autopilot.page_analysis import detect_question_fields

        questions = detect_question_fields(self._session_with_a_react_select())
        labels = [q.question.lower() for q in questions]
        assert labels.count("how did you hear about this job?") == 1

    def test_the_dropdown_interaction_wins_over_typing_into_it(self):
        # Typing into a closed react-select does nothing; opening it and
        # picking an option is the interaction that works.
        from careeros_autopilot.page_analysis import detect_question_fields

        questions = detect_question_fields(self._session_with_a_react_select())
        hear = next(q for q in questions if "hear about" in q.question.lower())
        assert hear.kind == "combobox"
        assert hear.selector == '[id="combo-1"]'

    def test_genuinely_different_questions_are_all_kept(self):
        from careeros_autopilot.page_analysis import detect_question_fields

        questions = detect_question_fields(self._session_with_a_react_select())
        assert len(questions) == 2
        assert any("why this company" in q.question.lower() for q in questions)


class TestChoiceGroupsAreNeverProfileFields:
    """Every profile-mapped field (name, email, phone) is WRITTEN to.

    A radio group never is. "Do you have a phone number?" classifies as PHONE
    and would then be text-filled, which raises — the same family of bug as
    text-filling an EEO radio.
    """

    def test_a_phone_shaped_radio_group_becomes_a_question_not_the_phone_field(self):
        from careeros_autopilot.page_analysis import detect_form_mapping

        session = FakeBrowserSession()
        session.set_fields(
            [
                {"selector": '[id="e"]', "type": "text", "label": "Email", "autocomplete": "email"},
                {
                    "selector": '[id="p1"]',
                    "type": "radio",
                    "name": "hasphone",
                    "label": "Do you have a phone number?",
                    "option_label": "Yes",
                },
                {
                    "selector": '[id="p2"]',
                    "type": "radio",
                    "name": "hasphone",
                    "label": "Do you have a phone number?",
                    "option_label": "No",
                },
            ]
        )
        session.set_buttons([{"selector": '[id="go"]', "accessible_name": "Submit Application"}])
        mapping = detect_form_mapping(session)
        assert mapping is not None
        # NOT wired up as the phone field...
        assert mapping.phone_selector is None
        # ...and offered as a choice question instead.
        question = next(q for q in mapping.question_fields if "phone" in q.question)
        assert question.kind == "choice"
        assert set(question.options) == {"yes", "no"}


class TestEveryFieldIsClaimedByExactlyOneSide:
    """A field claimed by BOTH the mapping and the question scan is written
    twice; a field claimed by NEITHER is silently unfillable. Both have
    happened, so both are pinned here."""

    def test_a_recognised_purpose_the_mapping_cannot_fill_stays_a_question(self):
        # "LinkedIn Profile" classifies as LINKEDIN — a purpose FormFieldMapping
        # has no slot for. Claiming it as a profile field meant it was filled by
        # nothing at all.
        from careeros_application_runner import FieldPurpose, map_fields
        from careeros_autopilot.page_analysis import is_question_field

        rows = [
            {
                "selector": '[id="li"]',
                "tag": "input",
                "type": "text",
                "label": "LinkedIn Profile",
                "name": "",
                "id_attr": "li",
                "aria_label": "",
                "placeholder": "",
                "autocomplete": "",
                "heading": "",
                "required": False,
                "disabled": False,
                "readonly": False,
                "options": [],
            },
        ]
        mapped = map_fields(rows)[0]
        assert mapped.purpose is FieldPurpose.LINKEDIN
        assert is_question_field(mapped), "a field the mapping cannot fill must be asked"

    def test_a_profile_field_the_mapping_does_fill_is_not_also_asked(self):
        from careeros_autopilot.page_analysis import detect_question_fields

        session = FakeBrowserSession()
        session.set_fields(
            [
                {
                    "selector": '[id="n"]',
                    "type": "text",
                    "label": "Full name",
                    "autocomplete": "name",
                },
                {"selector": '[id="e"]', "type": "text", "label": "Email", "autocomplete": "email"},
            ]
        )
        labels = [q.question.lower() for q in detect_question_fields(session)]
        assert "full name" not in labels
        assert "email" not in labels

    def test_the_answerer_can_answer_everything_left_as_a_question(self):
        # The contract behind MAPPED_PURPOSES: whatever the mapping does not
        # fill, the answerer must know how to answer.
        from careeros_application_runner import FieldPurpose as FP
        from careeros_autopilot.page_analysis import MAPPED_PURPOSES

        answerable_elsewhere = {
            FP.LINKEDIN,
            FP.GITHUB,
            FP.PORTFOLIO,
            FP.LOCATION,
            FP.CURRENT_EMPLOYER,
            FP.CURRENT_TITLE,
            FP.QUESTION,
        }
        assert set(FP) == MAPPED_PURPOSES | answerable_elsewhere
