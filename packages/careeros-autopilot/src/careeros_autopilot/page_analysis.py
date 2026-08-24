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
CAPTCHA_DETECTORS = [
    SelectorAppearsDetector("iframe[src*='recaptcha']", kind="captcha"),
    SelectorAppearsDetector("iframe[src*='hcaptcha']", kind="captcha"),
    SelectorAppearsDetector("iframe[src*='turnstile']", kind="captcha"),
    SelectorAppearsDetector(".g-recaptcha", kind="captcha"),
    SelectorAppearsDetector(".h-captcha", kind="captcha"),
]
LOGIN_WALL_DETECTORS = [
    SelectorAppearsDetector("input[type='password']", kind="login_required"),
]
DEFAULT_PROBLEM_DETECTORS = [*CAPTCHA_DETECTORS, *LOGIN_WALL_DETECTORS]

_EMAIL_SELECTORS = ["input[type='email']", "#email", "input[name*='email' i]"]
_FIRST_NAME_SELECTORS = ["#first_name", "input[name*='first' i]"]
_LAST_NAME_SELECTORS = ["#last_name", "input[name*='last' i]"]
_FULL_NAME_SELECTORS = [
    "input[autocomplete='name']",
    "input[name='name']",
    "input[name*='full' i]",
]
_PHONE_SELECTORS = ["input[type='tel']", "#phone", "input[name*='phone' i]"]
_RESUME_SELECTORS = ["input[type='file']"]
# The cover-letter TEXT field — must be a textarea we can type into. A bare
# "#cover_letter" is dangerous: on Greenhouse that id is an <input type="file">,
# and typing into a file input throws. Match textareas only; a file-based cover
# letter is simply left for the resume upload / a human, never force-filled.
_COVER_LETTER_SELECTORS = [
    "textarea[name*='cover' i]",
    "textarea#cover_letter",
    "textarea[name*='letter' i]",
]
_SUBMIT_SELECTORS = [
    "#submit_app",
    "#btn-submit",  # Lever
    "button[type='submit']",
    "input[type='submit']",
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
    for selector, kind in (("textarea", "text"), ("input[type='text']", "text")):
        try:
            elements = session.query_all(
                selector,
                extract={
                    "id": f"{selector}@id",
                    "label": f"{selector}@aria-label",
                    "placeholder": f"{selector}@placeholder",
                },
            )
        except Exception:
            continue
        for element in elements:
            element_id = element.get("id")
            question = element.get("label") or element.get("placeholder")
            if not element_id or not question:
                continue
            lowered = question.lower()
            if any(word in lowered for word in ("first name", "last name", "email", "phone")):
                continue
            css = f"#{element_id}"
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
        return "no application form or apply link found on the posting page"
    try:
        session.goto(apply_url)
    except Exception as exc:
        return f"could not open apply link {apply_url}: {exc}"
    _settle_for_form(session, apply_url)
    return None
