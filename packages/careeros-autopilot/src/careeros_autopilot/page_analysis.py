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

from careeros_application_runner import FormFieldMapping, QuestionField
from careeros_browser import BrowserSession
from careeros_human_in_the_loop import SelectorAppearsDetector
from careeros_job_providers import JobPosting

# Hosts whose URLs are themselves application forms. Lever serves EU postings
# from jobs.eu.lever.co; JazzHR uses <company>.applytojob.com.
_ATS_HOST_RE = re.compile(
    r"(boards\.greenhouse\.io|job-boards\.greenhouse\.io|jobs\.(eu\.)?lever\.co|"
    r"jobs\.ashbyhq\.com|apply\.workable\.com|jobs\.smartrecruiters\.com|"
    r"\.recruitee\.com|jobs\.jobvite\.com|\.bamboohr\.com|\.applytojob\.com)",
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
_BOT_PROTECTION_SELECTORS = [
    "text=/just a moment/i",
    "#challenge-form",
    "text=/verify you are human/i",
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
        links = session.query_all("a", extract={"href": "a@href"})
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
        fields.append(QuestionField(selector=selector, question=question, kind="combobox"))

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


def detect_form_mapping(
    session: BrowserSession, *, require_submit: bool = True
) -> FormFieldMapping | None:
    """Build a mapping from what's visibly on the page, or None.

    ``require_submit=False`` (prepare-and-review) accepts a form as soon as it
    has a fillable email field, even if no submit button is exposed — a human
    reviews and submits, so we only need somewhere to put the candidate's data.
    """
    email = _first_visible(session, _EMAIL_SELECTORS)
    submit = _first_visible(session, _SUBMIT_SELECTORS)
    if email is None:
        return None
    if submit is None:
        if require_submit:
            return None
        # Placeholder — never clicked in prepare mode; the human submits.
        submit = "button[type='submit']"

    first_name = _first_visible(session, _FIRST_NAME_SELECTORS)
    last_name = _first_visible(session, _LAST_NAME_SELECTORS)
    full_name = None if first_name else _first_visible(session, _FULL_NAME_SELECTORS)

    return FormFieldMapping(
        email_selector=email,
        first_name_selector=first_name,
        last_name_selector=last_name,
        full_name_selector=full_name,
        phone_selector=_first_visible(session, _PHONE_SELECTORS),
        resume_upload_selector=_first_visible(session, _RESUME_SELECTORS),
        cover_letter_selector=_first_visible(session, _COVER_LETTER_SELECTORS),
        question_fields=detect_question_fields(session),
        submit_selector=submit,
        success_selector=GENERIC_SUCCESS_SELECTOR,
    )


def _settle_for_form(session: BrowserSession, url: str) -> None:
    """On a known ATS host, give a client-rendered form (Ashby/Greenhouse are
    React apps) a moment to appear before we inspect the page. No-op on other
    hosts, so aggregator pages that will never hold a form add no latency.
    """
    if not _ATS_HOST_RE.search(url or ""):
        return
    try:
        # Any core field appearing means the form has rendered. The fake test
        # session raises immediately when absent, so this only waits for real.
        session.wait_for_selector("input[type='email']", timeout_ms=6000)
    except Exception:
        return


def prepare_application_page(session: BrowserSession, posting: JobPosting) -> str | None:
    """Navigate to the posting and onward to its application form.

    Returns an error reason, or None once a page that may hold the form
    is loaded. Never creates accounts or works around access walls —
    those are reported via the problem detectors afterwards.
    """
    # Go straight to the employer's real apply form when the provider gave us
    # one (RemoteOK/WorkingNomads), instead of the aggregator listing page.
    target = posting.apply_url or posting.url
    try:
        session.goto(target)
    except Exception as exc:
        return f"could not open {target}: {exc}"

    if _first_visible(session, _BOT_PROTECTION_SELECTORS) is not None:
        return "the site is showing a bot-protection challenge — a human must apply here"

    _settle_for_form(session, target)
    if detect_form_mapping(session) is not None:
        return None  # the posting page itself is the form

    # Prefer a real apply link on the page; otherwise derive the conventional
    # form URL for known ATS hosts (Ashby/Lever route the form to a subpath the
    # posting page has no crawlable <a> to).
    apply_url = find_apply_url(session) or ats_apply_url(target)
    if apply_url is None:
        # Distinguish "we could not find the form" from "there is no hosted
        # form to find". Some ATS customers (Stripe is one) publish through
        # Greenhouse but redirect every application to their own careers site,
        # so the posting URL lands somewhere off the ATS host entirely. Saying
        # "no form found" there reads as a CareerOS bug when it is a fact about
        # the employer, and it sends a user hunting for a fault that is not
        # ours to fix.
        landed = session.current_url or ""
        # The posting came from an ATS provider, so a hosted form was expected;
        # landing off every known ATS host means the employer took us to their
        # own site. Checked against the POSTING's source rather than the URL,
        # because these employers publish an off-host apply URL in the first
        # place - the redirect has already happened by the time we see it.
        from_ats = (posting.source_provider or "").startswith("ats:") or _ATS_HOST_RE.search(
            target or ""
        )
        if from_ats and not _ATS_HOST_RE.search(landed):
            return (
                "this employer redirects applications to its own careers site "
                f"({landed.split('/')[2] if '://' in landed else landed}) — "
                "there is no hosted ATS form to fill"
            )
        return "no application form or apply link found on the posting page"
    try:
        session.goto(apply_url)
    except Exception as exc:
        return f"could not open apply link {apply_url}: {exc}"
    _settle_for_form(session, apply_url)
    return None
