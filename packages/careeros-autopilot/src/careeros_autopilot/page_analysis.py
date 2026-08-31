"""Live-page analysis: find the real application form from a job posting
page, and build a FormFieldMapping by inspecting what's actually there.

Selector sets cover the major single-page ATS platforms (Greenhouse,
Lever, Ashby, Workable) plus generic fallbacks. If a page doesn't
yield at least an email field and a submit button, no mapping is
returned and the application is left for a human — the autopilot never
guesses blindly.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from careeros_application_runner import (
    FieldPurpose,
    FormFieldMapping,
    MappedField,
    QuestionField,
    find_submit_control,
    map_fields,
    normalize_label,
)
from careeros_browser import BrowserSession
from careeros_human_in_the_loop import SelectorAppearsDetector
from careeros_job_providers import JobPosting

# Hosts whose URLs are themselves application forms. Lever serves EU postings
# from jobs.eu.lever.co; JazzHR uses <company>.applytojob.com.
_ATS_HOST_RE = re.compile(
    r"(boards\.greenhouse\.io|job-boards\.greenhouse\.io|jobs\.(eu\.)?lever\.co|"
    r"jobs\.ashbyhq\.com|apply\.workable\.com|jobs\.smartrecruiters\.com|"
    r"\.recruitee\.com|jobs\.jobvite\.com|\.bamboohr\.com|\.applytojob\.com|"
    r"smartrecruiters\.com/oneclick-ui)",
    re.IGNORECASE,
)

# Blocking conditions the autopilot must never try to get around: a captcha,
# or a login/signup wall (a visible password field means exactly that).
#
# Only INTERACTIVE captchas count — the ones a human must actually click. We do
# NOT match the generic "recaptcha" iframe, because reCAPTCHA v3 keeps a visible
# badge on the page at all times with no challenge to solve; matching it made
# the autopilot pause pointlessly on forms that submit fine on their own. The
# v2 checkbox (api2/anchor) and image challenge (api2/bframe) are the real,
# human-solvable frames; hCaptcha/Turnstile challenge frames likewise.
_CAPTCHA = "a captcha challenge"
CAPTCHA_DETECTORS = [
    SelectorAppearsDetector("iframe[src*='api2/anchor']", kind="captcha", description=_CAPTCHA),
    SelectorAppearsDetector("iframe[src*='api2/bframe']", kind="captcha", description=_CAPTCHA),
    SelectorAppearsDetector("iframe[src*='hcaptcha.com']", kind="captcha", description=_CAPTCHA),
    SelectorAppearsDetector(
        "iframe[src*='challenges.cloudflare.com']", kind="captcha", description=_CAPTCHA
    ),
    SelectorAppearsDetector(".h-captcha iframe", kind="captcha", description=_CAPTCHA),
    # DataDome. Observed live on SmartRecruiters' oneclick-ui apply pages
    # (2026-08-31): the apply URL serves a challenge and NO form. Without this
    # the run reported "no fillable form found on the page or in any frame",
    # which sends the user looking for a CareerOS bug — the form is not missing,
    # it is behind an anti-bot wall we must not try to get around.
    SelectorAppearsDetector(
        "iframe[src*='captcha-delivery.com']", kind="captcha", description=_CAPTCHA
    ),
]
LOGIN_WALL_DETECTORS = [
    SelectorAppearsDetector(
        "input[type='password']", kind="login_required", description="a login/sign-in wall"
    ),
]
DEFAULT_PROBLEM_DETECTORS = [*CAPTCHA_DETECTORS, *LOGIN_WALL_DETECTORS]

# Email is the anchor field detection keys off, so it must not depend on a
# single markup convention. Modern Greenhouse renders it as
# <input type="text" id="email" autocomplete="email"> — no type="email" at all,
# which is why a form that was perfectly fillable looked like no form at all.
_EMAIL_SELECTORS = [
    "input[type='email']",
    "#email",
    "input[autocomplete='email']",
    "input[name*='email' i]",
    "input[id*='email' i]",
    "input[aria-label*='email' i]",
    "input[placeholder*='email' i]",
]
_FIRST_NAME_SELECTORS = ["#first_name", "input[name*='first' i]"]
_LAST_NAME_SELECTORS = ["#last_name", "input[name*='last' i]"]
_FULL_NAME_SELECTORS = [
    "input[autocomplete='name']",
    "input[name='name']",
    "input[name*='full' i]",
]
_PHONE_SELECTORS = ["input[type='tel']", "#phone", "input[name*='phone' i]"]
# Résumé upload — prefer a file input clearly for the résumé/CV, and NEVER a
# cover-letter file input (a plain "input[type='file']" match was uploading the
# résumé into the cover-letter slot on forms that have both).
_RESUME_SELECTORS = [
    "input[type='file'][name*='resume' i]",
    "input[type='file'][id*='resume' i]",
    "input[type='file'][name*='cv' i]",
    "input[type='file'][id*='cv' i]",
    # Generic fallback: any file input that is NOT a cover-letter upload. If
    # even this finds nothing, we skip the résumé rather than risk uploading it
    # to the wrong field.
    "input[type='file']:not([id*='cover' i]):not([name*='cover' i])"
    ":not([id*='letter' i]):not([name*='letter' i])",
]
# The cover-letter TEXT field — must be a textarea we can type into. A bare
# "#cover_letter" is dangerous: on Greenhouse that id is an <input type="file">,
# and typing into a file input throws. Match textareas only; a file-based cover
# letter is simply left for the resume upload / a human, never force-filled.
_COVER_LETTER_SELECTORS = [
    "textarea[name*='cover' i]",
    "textarea#cover_letter",
    "textarea[name*='letter' i]",
]
# Submit control. Order matters, and the LAST entry is deliberately last.
#
# On a real Ashby form there are FORTY `button[type=submit]` elements: every
# "Upload file" control and every Yes/No option renders as one, and the actual
# "Submit Application" button is the last of them. Matching that bare selector
# picked "Upload file" — so the autopilot's submit click would have opened a
# file dialog while believing it had applied. The text-matching entries are
# what identify the real control; the bare type match survives only as a final
# fallback for forms with a single unlabelled button.
_SUBMIT_SELECTORS = [
    "#submit_app",  # Greenhouse
    "#btn-submit",  # Lever
    "button:has-text('Submit Application')",
    "button:has-text('Submit application')",
    "button:has-text('Submit Application ')",
    "input[type='submit'][value*='Submit' i]",
    "button:text-is('Submit')",
    "button:has-text('Apply for this job')",
    "button:has-text('Send application')",
    "input[type='submit']",
    "button[type='submit']",
]

# Bot-protection interstitials (e.g. Cloudflare). The autopilot never
# tries to get past these — it reports them so a human can take over.
#
# Matched on the CURRENT copy, not the copy these vendors used when this list
# was written. Observed live on apply.workable.com (2026-08-31) after repeated
# automated visits: Cloudflare Turnstile now says "Just a sec!" and "Verifying
# you are human", so "just a moment" and "verify you are human" both missed and
# the run reported "no application form or apply link found on the posting
# page" — sending the user to look for a CareerOS bug when the form was simply
# behind a wall we must not try to get around.
#
# The challenge IFRAMES are the durable signal: vendor marketing copy changes,
# the challenge host does not.
_BOT_PROTECTION_SELECTORS = [
    "iframe[src*='challenges.cloudflare.com']",
    "iframe[src*='captcha-delivery.com']",
    "iframe[src*='hcaptcha.com']",
    "#challenge-form",
    "text=/just a (moment|sec)/i",
    "text=/verif(y|ying) you are human/i",
    "text=/checking your browser/i",
]

# Playwright text-engine selector: matches common confirmation copy.
GENERIC_SUCCESS_SELECTOR = "text=/thank(s| you)|application (received|submitted)|success/i"


#: Placeholder text that describes the INPUT rather than asking anything. Used
#: as a question label it produces nonsense answers, so it is discarded.
_GENERIC_PLACEHOLDERS = (
    "type here",
    "start typing",
    "pick date",
    "select...",
    "select an option",
    "choose...",
    "enter value",
    "your answer",
)


def _is_generic_placeholder(text: str) -> bool:
    stripped = text.strip().lower().rstrip(".…")
    return any(stripped.startswith(marker) for marker in _GENERIC_PLACEHOLDERS)


def _first_visible(session: BrowserSession, selectors: list[str]) -> str | None:
    for selector in selectors:
        try:
            if session.is_visible(selector):
                return selector
        except Exception:
            continue
    return None


def find_apply_url(session: BrowserSession) -> str | None:
    """From a job posting page, the most likely link to the real form."""
    try:
        # "@href" reads the attribute off the MATCHED element. The previous
        # "a@href" asked for a nested <a> inside each <a>, which never exists —
        # so this function silently found no links at all, on every site, and
        # every ATS whose form lives behind an apply link (SmartRecruiters'
        # localised "Jetzt bewerben", Workday, Recruitee) was unreachable. The
        # same trap is documented on detect_question_fields below.
        links = session.query_all("a", extract={"href": "@href"})
    except Exception:
        return None
    hrefs = [link.get("href") or "" for link in links]
    for href in hrefs:
        if _ATS_HOST_RE.search(href):
            return href
    for href in hrefs:
        path = href.split("?")[0].rstrip("/")
        # Lever uses …/apply; Ashby routes the form to …/application.
        if path.endswith("/apply") or path.endswith("/application"):
            return href
    return None


def ats_apply_url(posting_url: str) -> str | None:
    """The conventional application-form URL for a known ATS posting, when the
    posting page routes to a separate form (a React app with no <a> to follow).
    None for hosts whose form is inline on the posting page (e.g. Greenhouse).
    """
    base = posting_url.split("?")[0].rstrip("/")
    if not base:
        return None
    if "jobs.ashbyhq.com" in base and not base.endswith("/application"):
        return f"{base}/application"
    # Lever serves some postings from jobs.eu.lever.co; both take /apply.
    if re.search(r"jobs\.(eu\.)?lever\.co", base) and not base.endswith("/apply"):
        return f"{base}/apply"
    return None


def detect_question_fields(session: BrowserSession) -> list[QuestionField]:
    """Find extra application questions on the page: inputs/textareas that
    carry a readable label (aria-label / placeholder), keyed by a stable
    id selector, excluding the standard name/email/phone fields.

    Uses whatever the live browser exposes via query_all; the fake session
    in tests returns queued results, so this stays fully testable.
    """
    fields: list[QuestionField] = []
    seen: set[str] = set()
    #: Question LABELS already claimed. A selector set is not enough: two scans
    #: can reach the same widget through different elements, and then the same
    #: question is answered twice — once correctly and once destructively.
    asked: set[str] = set()

    # Standard fields the mapping already fills — never re-ask them as questions.
    _standard = ("first name", "last name", "email", "phone", "resume", "cv", "cover letter")

    # A <label for="id"> gives the question text for most real forms (aria-label
    # and placeholder are the exception, not the rule).
    labels_by_for: dict[str, str] = {}
    try:
        for label in session.query_all("label", extract={"for": "@for", "text": ""}):
            target = (label.get("for") or "").strip()
            text = (label.get("text") or "").strip()
            if target and text:
                labels_by_for[target] = text
    except Exception:
        labels_by_for = {}

    # Custom (React/ARIA) dropdowns — the "Select…" widgets that aren't native
    # <select> and so need a click-and-pick interaction, not a plain fill.
    #
    # Runs FIRST, ahead of the generic text/select scan below: a real
    # react-select's focusable input has type="text" as an implementation
    # detail, with a real usable aria-label — so it also matches
    # "input[type='text']" below. If that scan ran first it would claim the
    # selector as a plain text field before detect_comboboxes() got a
    # chance, and fill_application_form later calling .fill() on a closed
    # dropdown types into it without ever selecting an option, i.e. silently
    # does nothing (verified against a live Greenhouse form, 2026-08-26 —
    # every EEO/sponsorship dropdown question was affected).
    try:
        comboboxes = session.detect_comboboxes()
    except Exception:
        comboboxes = []
    for combobox in comboboxes:
        selector = (combobox.get("selector") or "").strip()
        question = (combobox.get("question") or "").strip()
        if not selector or not question or selector in seen:
            continue
        seen.add(selector)
        # Claim the QUESTION too, not just the selector. The two scans below
        # reach the same react-select through a different element and so
        # produce a different selector for it — observed live on Greenhouse
        # (2026-08-31): "How did you hear about this job?" was answered twice,
        # once by opening the dropdown and once by typing into its inner input,
        # and the typed one silently discarded the value.
        asked.add(normalize_label(question))
        fields.append(QuestionField(selector=selector, question=question, kind="combobox"))

    # The semantic scan: every field the DOM exposes that is NOT one of the
    # standard identity fields is a question. It runs after comboboxes (which
    # have already claimed their selectors) and before the legacy scan, and it
    # is the only path that carries the form's own `required` flag through —
    # which is what separates "a question a human should answer" from "a
    # question that blocks submission".
    try:
        descriptors = session.detect_fields()
    except Exception:
        descriptors = []
    for mapped in map_fields(descriptors):
        # is_question_field, not a bare purpose check: the mapping uses the
        # same rule, so a field cannot be claimed by both (written twice) or
        # by neither (silently unfillable).
        if not is_question_field(mapped):
            # A PROFILE field (name, email, phone). Claim it so the legacy
            # scan below cannot also offer it as a question: its own exclusion
            # list never covered "full name", so a Lever form's single name
            # input was both mapped as the name field AND asked as a question,
            # and then written twice.
            if mapped.selector:
                seen.add(mapped.selector)
            if mapped.label:
                asked.add(normalize_label(mapped.label))
            continue
        if not mapped.label:
            continue
        if mapped.selector in seen or _is_generic_placeholder(mapped.label):
            continue
        if normalize_label(mapped.label) in asked:
            continue
        seen.add(mapped.selector)
        asked.add(normalize_label(mapped.label))
        fields.append(
            QuestionField(
                selector=mapped.selector,
                question=mapped.label,
                # "choice" carries through as itself: a radio group is answered
                # by clicking an option, and calling it "text" is what made
                # fill() raise "Input of type radio cannot be filled".
                kind=(mapped.kind if mapped.kind in ("text", "select", "choice") else "text"),
                required=mapped.required,
                options=list(mapped.options),
                option_selectors=dict(mapped.option_selectors),
            )
        )

    # NOTE: "@attr" extracts the element's OWN attribute; a bare "textarea@id"
    # would look for a *nested* textarea and always miss — which is why live
    # forms used to yield no questions at all.
    for selector, kind in (
        ("textarea", "text"),
        ("input[type='text']", "text"),
        ("select", "select"),
    ):
        try:
            elements = session.query_all(
                selector,
                extract={"id": "@id", "label": "@aria-label", "placeholder": "@placeholder"},
            )
        except Exception:
            continue
        for element in elements:
            element_id = element.get("id")
            # A real <label for=…> beats a placeholder. Ashby renders every
            # free-text question with the placeholder "Type here..." and puts
            # the actual question in the label; reading the placeholder first
            # meant the answerer was asked to answer "Type here...", five times
            # per form. aria-label still wins over both — where it exists it is
            # the most specific.
            question = (
                element.get("label")
                or (labels_by_for.get(element_id) if element_id else None)
                or element.get("placeholder")
            )
            if not element_id or not question:
                continue
            if _is_generic_placeholder(question):
                # No usable label anywhere: a question we cannot read is one we
                # must not answer, so it is left for a human rather than fed to
                # the answerer as literal prompt text.
                continue
            lowered = question.lower()
            if any(word in lowered for word in _standard):
                continue
            # Attribute selector, not "#id": some ATS use all-numeric ids
            # (e.g. id="4001209002"), and "#4001209002" is INVALID CSS and
            # throws when filled — which crashed whole cycles.
            css = f'[id="{element_id}"]'
            if css in seen:
                continue
            seen.add(css)
            fields.append(QuestionField(selector=css, question=question, kind=kind))

    return fields


def detect_submit_selector(session: BrowserSession) -> tuple[str | None, str]:
    """The control that submits the application, and why it was chosen.

    Semantic classification first (see ``form_semantics``): it reads the
    control's accessible name, role, disabled state and whether it belongs to
    a file-upload widget, which is the only way to tell "Upload file" from
    "Submit Application" on a form where both render as ``button[type=submit]``.

    The old selector list survives as a fallback for pages whose DOM we cannot
    evaluate — but it is the fallback now, not the primary, because on a real
    Ashby form it picked an upload button.
    """
    try:
        buttons = session.detect_buttons()
    except Exception:
        buttons = []
    if buttons:
        found = find_submit_control(buttons)
        if found is not None and not found.disabled:
            return found.selector, found.reason
        if found is not None:
            return found.selector, found.reason
        # Buttons were readable and NONE of them submits. That is a real
        # answer ("this step does not submit"), not a reason to fall through
        # to a selector list that would match one of the upload buttons.
        return None, "no control on this page has submit semantics"

    selector = _first_visible(session, _SUBMIT_SELECTORS)
    if selector is None:
        return None, "no submit control matched"
    return selector, "matched a known submit selector (DOM not inspectable)"


def _semantic_mapping(session: BrowserSession) -> dict | None:
    """Field selectors by purpose, classified from every DOM label signal.

    Returns None when the page exposes no fields to classify, so the caller
    falls back to selector probing rather than reporting an empty form.
    """
    try:
        descriptors = session.detect_fields()
    except Exception:
        return None
    if not descriptors:
        return None

    by_purpose: dict[FieldPurpose, str] = {}
    questions: list[MappedField] = []
    for mapped in map_fields(descriptors):
        if is_question_field(mapped):
            questions.append(mapped)
        elif _kind_matches_purpose(mapped) and mapped.purpose not in by_purpose:
            # First wins: forms repeat a field (a hidden duplicate, a second
            # "email" for confirmation) and the first is the real one.
            by_purpose[mapped.purpose] = mapped.selector
    return {"by_purpose": by_purpose, "questions": questions}


def _kind_matches_purpose(mapped: MappedField) -> bool:
    """Whether this field can actually be written the way its purpose needs.

    Only the two purposes where the distinction is dangerous are constrained:
    a résumé must go to a file input (uploading to a text box is impossible),
    and a cover letter must go to a text box (typing into a file input raises
    and fails the whole fill).
    """
    if mapped.purpose is FieldPurpose.RESUME:
        return mapped.kind == "file"
    if mapped.purpose is FieldPurpose.COVER_LETTER:
        return mapped.kind == "text"
    # Every profile-mapped field (name, email, phone) is written to. A radio or
    # checkbox group never is — "Do you have a phone number?" classifies as
    # PHONE and would then be text-filled, which raises. Choice groups are
    # always answered as questions instead.
    if mapped.kind == "choice":
        return False
    return mapped.kind != "file"


#: The only purposes ``FormFieldMapping`` actually fills. Everything else the
#: classifier can recognise — LinkedIn, GitHub, portfolio, location, current
#: employer/title — has no slot on the mapping, so it must stay a QUESTION and
#: be answered by the answerer, which knows all of them.
#:
#: Getting this wrong is silent: "LinkedIn Profile" classified as LINKEDIN, was
#: claimed as a profile field, and was then filled by nothing at all.
MAPPED_PURPOSES = frozenset(
    {
        FieldPurpose.FIRST_NAME,
        FieldPurpose.LAST_NAME,
        FieldPurpose.FULL_NAME,
        FieldPurpose.EMAIL,
        FieldPurpose.PHONE,
        FieldPurpose.RESUME,
        FieldPurpose.COVER_LETTER,
    }
)


def is_question_field(mapped: MappedField) -> bool:
    """Whether this field should be answered rather than filled from the profile.

    Shared by the mapping and the question scan so the two cannot disagree
    about the same field — a field claimed by neither is silently unfillable,
    and a field claimed by both gets written twice.

    Knowing WHAT a field is for is not enough; how it must be WRITTEN matters
    just as much. A text field whose purpose we cannot serve directly ("Resume
    URL") is still a real field, so it becomes a question. A file input we
    cannot classify is neither: there is no safe way to guess what belongs in
    it, and uploading the wrong document is worse than leaving it for a human.
    """
    if mapped.purpose is FieldPurpose.QUESTION:
        return True
    if mapped.purpose not in MAPPED_PURPOSES:
        return True
    if _kind_matches_purpose(mapped):
        return False
    return mapped.kind != "file" and bool(mapped.label)


def detect_form_mapping(
    session: BrowserSession, *, require_submit: bool = True
) -> FormFieldMapping | None:
    """Build a mapping from what's visibly on the page, or None.

    ``require_submit=False`` (prepare-and-review) accepts a form as soon as it
    has a fillable email field, even if no submit button is exposed — a human
    reviews and submits, so we only need somewhere to put the candidate's data.
    """
    semantic = _semantic_mapping(session)
    by_purpose = semantic["by_purpose"] if semantic else {}

    # Semantic classification first, selector probing as the fallback for each
    # field independently: a page can expose some fields to the DOM scan and
    # not others, and losing a phone number because the scan was partial is a
    # worse outcome than probing twice.
    email = by_purpose.get(FieldPurpose.EMAIL) or _first_visible(session, _EMAIL_SELECTORS)
    if email is None:
        return None

    submit, _why = detect_submit_selector(session)
    if submit is None:
        if require_submit:
            return None
        # Placeholder — never clicked in prepare mode; the human submits.
        submit = "button[type='submit']"

    first_name = by_purpose.get(FieldPurpose.FIRST_NAME) or _first_visible(
        session, _FIRST_NAME_SELECTORS
    )
    last_name = by_purpose.get(FieldPurpose.LAST_NAME) or _first_visible(
        session, _LAST_NAME_SELECTORS
    )
    full_name = None
    if not first_name:
        full_name = by_purpose.get(FieldPurpose.FULL_NAME) or _first_visible(
            session, _FULL_NAME_SELECTORS
        )

    return FormFieldMapping(
        email_selector=email,
        first_name_selector=first_name,
        last_name_selector=last_name,
        full_name_selector=full_name,
        phone_selector=by_purpose.get(FieldPurpose.PHONE)
        or _first_visible(session, _PHONE_SELECTORS),
        resume_upload_selector=by_purpose.get(FieldPurpose.RESUME)
        or _first_visible(session, _RESUME_SELECTORS),
        cover_letter_selector=by_purpose.get(FieldPurpose.COVER_LETTER)
        or _first_visible(session, _COVER_LETTER_SELECTORS),
        question_fields=detect_question_fields(session),
        submit_selector=submit,
        success_selector=GENERIC_SUCCESS_SELECTOR,
    )


@dataclass
class FormLocation:
    """Where the application form actually is, and how to fill it.

    ``session`` is the document the form lives in — the page for most ATSes,
    a frame for the ones (SmartRecruiters) that render the form in an iframe.
    Every selector in ``mapping`` is resolved against THAT session and is
    meaningless against any other, which is exactly why the two travel
    together rather than the mapping being returned alone.
    """

    session: BrowserSession
    mapping: FormFieldMapping
    #: How the frame was reached, empty for the main document. Kept so a
    #: failed fill can say WHICH document it failed in.
    frame_path: tuple[str, ...] = ()

    @property
    def in_frame(self) -> bool:
        return bool(self.frame_path)

    def describe(self) -> str:
        if not self.frame_path:
            return "the page itself"
        return "an iframe (" + " → ".join(self.frame_path) + ")"


#: How deep to search for a form. Two levels covers every real case seen
#: (SmartRecruiters nests its upload widget inside the application frame) and
#: bounds the cost on ad-heavy pages, which can carry a dozen frames.
MAX_FRAME_DEPTH = 2


def locate_form(
    session: BrowserSession,
    *,
    require_submit: bool = True,
    max_depth: int = MAX_FRAME_DEPTH,
) -> FormLocation | None:
    """The form on this page, wherever it lives — including inside an iframe.

    A CSS selector reaches one document, so a form rendered in an iframe is
    not merely harder to find: it is unreachable, and looks identical to a
    page with no form at all. That is what made SmartRecruiters report "no
    fillable form found" on pages whose form was right there.

    The page is always checked first, so nothing about the existing ATSes
    changes and no frame is even enumerated on a form that is already
    reachable.
    """
    mapping = detect_form_mapping(session, require_submit=require_submit)
    if mapping is not None:
        return FormLocation(session=session, mapping=mapping, frame_path=())

    if max_depth <= 0:
        return None

    try:
        handles = session.frames()
    except Exception:
        return None

    for handle in handles:
        if handle.depth > max_depth:
            continue
        try:
            scoped = session.frame(index=handle.index)
        except Exception:
            continue
        if scoped is None:
            continue
        found = detect_form_mapping(scoped, require_submit=require_submit)
        if found is not None:
            return FormLocation(
                session=scoped,
                mapping=found,
                frame_path=tuple(getattr(scoped, "frame_path", ()) or (handle.describe(),)),
            )
    return None


def _settle_for_form(session: BrowserSession, url: str) -> None:
    """On a known ATS host, give a client-rendered form (Ashby/Greenhouse are
    React apps) a moment to appear before we inspect the page. No-op on other
    hosts, so aggregator pages that will never hold a form add no latency.
    """
    if not _ATS_HOST_RE.search(url or ""):
        return
    # Waiting specifically for input[type='email'] contradicted our own
    # detection: modern Greenhouse renders email as <input type="text"
    # autocomplete="email">, which is documented ten lines above _EMAIL_SELECTORS
    # and was still the thing this waited for. On a form that renders slowly and
    # uses no type=email, the wait expired, the scan ran against an empty page,
    # and the result was "no application form found" on a page that had one.
    #
    # ONE wait on a combined selector rather than several in sequence: any
    # visible field means the form has rendered, and four six-second waits on a
    # page that will never render is nearly half a minute per posting. The fake
    # test session raises immediately when absent, so this only waits for real.
    try:
        session.wait_for_selector("input:not([type='hidden']), textarea, select", timeout_ms=6000)
    except Exception:
        return


class ApplicationRoute(StrEnum):
    """Where a posting's application actually lives.

    The distinction that matters: an employer whose Greenhouse posting sends
    applicants to its own careers site is not a CareerOS failure and not a
    Greenhouse failure. Reporting it as "no form found" reads as a bug, and
    sends the user hunting for a fault that is not ours to fix. Three of the
    four sampled Greenhouse employers were exactly this case.
    """

    #: The form is on the ATS's own host and we can fill it.
    ATS_HOSTED = "ats_hosted"
    #: The employer routes applications to its own site, which we reached and
    #: found a fillable form on.
    EXTERNAL = "external"
    #: The employer routes applications off-ATS to somewhere we cannot drive
    #: (a login wall, a bespoke multi-step portal, a page with no form).
    #: A fact about the employer, NOT a failure of the integration.
    EXTERNAL_UNSUPPORTED = "external_unsupported"
    #: We could not tell. Kept separate so it is never quietly counted as
    #: either a success or an employer's fault.
    UNKNOWN = "unknown"


@dataclass
class PreparationResult:
    """What happened trying to reach a posting's application form.

    Carries enough to write the message the user should actually see: what was
    reached, why it stopped, and whether anyone can do anything about it.
    """

    route: ApplicationRoute
    #: None when a page that may hold the form is loaded.
    error: str | None = None
    #: Where the browser ended up. The single most useful piece of evidence.
    landed_url: str = ""
    #: Whether a human could complete this application by hand.
    human_can_continue: bool = True

    @property
    def ok(self) -> bool:
        return self.error is None

    @property
    def is_our_problem(self) -> bool:
        """Whether this counts against CareerOS's ATS coverage.

        An external redirect does not: the integration worked, the employer
        simply does not host its application there.
        """
        return self.route not in (
            ApplicationRoute.EXTERNAL,
            ApplicationRoute.EXTERNAL_UNSUPPORTED,
        )


def classify_route(posting: JobPosting, landed_url: str, *, form_found: bool) -> ApplicationRoute:
    """Which route this posting's application took.

    ``landed_url`` is where the browser actually ended up, which is the only
    thing that reflects a redirect — the posting's own URL was already
    off-host in these cases, so it cannot tell us.
    """
    on_ats_host = bool(_ATS_HOST_RE.search(landed_url or ""))
    if on_ats_host:
        return ApplicationRoute.ATS_HOSTED if form_found else ApplicationRoute.UNKNOWN

    # Off the ATS hosts. A form we found here is a real, fillable application
    # on the employer's own site — that is a supported external route, not a
    # second-class one.
    if form_found:
        return ApplicationRoute.EXTERNAL

    # No form, off-host. This is only an EMPLOYER's redirect if the posting
    # came from an ATS in the first place: that is the Greenhouse-customer
    # case where the integration worked and the company simply hosts its
    # applications elsewhere. Everything else is us failing to find a form,
    # which must not be dressed up as the employer's doing.
    came_from_ats = bool(
        (posting.source_provider or "").startswith("ats:")
        or _ATS_HOST_RE.search(posting.url or "")
        or _ATS_HOST_RE.search(posting.apply_url or "")
    )
    return ApplicationRoute.EXTERNAL_UNSUPPORTED if came_from_ats else ApplicationRoute.UNKNOWN


def prepare_application(session: BrowserSession, posting: JobPosting) -> PreparationResult:
    """Navigate to the posting and onward to its application form.

    Never creates accounts or works around access walls — those are reported
    via the problem detectors afterwards.
    """
    # Go straight to the employer's real apply form when the provider gave us
    # one (RemoteOK/WorkingNomads), instead of the aggregator listing page.
    target = posting.apply_url or posting.url
    try:
        session.goto(target)
    except Exception as exc:
        return PreparationResult(
            route=ApplicationRoute.UNKNOWN,
            error=f"could not open {target}: {exc}",
            landed_url=target,
            # We never reached the page, so we cannot say a human would fare
            # better — but they should try, because a transport failure here
            # is usually ours (a timeout), not the site refusing.
            human_can_continue=True,
        )

    landed = session.current_url or target
    if _first_visible(session, _BOT_PROTECTION_SELECTORS) is not None:
        return PreparationResult(
            route=classify_route(posting, landed, form_found=False),
            error="the site is showing a bot-protection challenge — a human must apply here",
            landed_url=landed,
        )

    _settle_for_form(session, target)
    if locate_form(session, require_submit=False) is not None:
        # The posting page itself is (or contains) the form.
        landed = session.current_url or target
        return PreparationResult(
            route=classify_route(posting, landed, form_found=True), landed_url=landed
        )

    # Prefer a real apply link on the page; otherwise derive the conventional
    # form URL for known ATS hosts (Ashby/Lever route the form to a subpath the
    # posting page has no crawlable <a> to).
    apply_url = find_apply_url(session) or ats_apply_url(target)
    if apply_url is None:
        landed = session.current_url or target
        route = classify_route(posting, landed, form_found=False)
        if route is ApplicationRoute.EXTERNAL_UNSUPPORTED:
            host = landed.split("/")[2] if "://" in landed else landed
            return PreparationResult(
                route=route,
                error=(
                    f"this employer routes applications to its own careers site ({host}) — "
                    "there is no hosted ATS form to fill, so this one has to be done by hand"
                ),
                landed_url=landed,
                human_can_continue=True,
            )
        return PreparationResult(
            route=route,
            error="no application form or apply link found on the posting page",
            landed_url=landed,
        )

    try:
        session.goto(apply_url)
    except Exception as exc:
        return PreparationResult(
            route=ApplicationRoute.UNKNOWN,
            error=f"could not open apply link {apply_url}: {exc}",
            landed_url=apply_url,
        )
    _settle_for_form(session, apply_url)
    landed = session.current_url or apply_url
    return PreparationResult(
        route=classify_route(
            posting, landed, form_found=locate_form(session, require_submit=False) is not None
        ),
        landed_url=landed,
    )


def prepare_application_page(session: BrowserSession, posting: JobPosting) -> str | None:
    """``prepare_application`` for callers that only need the error string.

    Kept because the executor's ``PagePreparer`` contract is "an error reason,
    or None". New code should use ``prepare_application`` and read the route.
    """
    return prepare_application(session, posting).error
