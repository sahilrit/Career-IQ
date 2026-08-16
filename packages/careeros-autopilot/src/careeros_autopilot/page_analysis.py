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

from careeros_application_runner import FormFieldMapping
from careeros_browser import BrowserSession
from careeros_human_in_the_loop import SelectorAppearsDetector
from careeros_job_providers import JobPosting

# Hosts whose URLs are themselves application forms.
_ATS_HOST_RE = re.compile(
    r"(boards\.greenhouse\.io|job-boards\.greenhouse\.io|jobs\.lever\.co|"
    r"jobs\.ashbyhq\.com|apply\.workable\.com|jobs\.smartrecruiters\.com|"
    r"\.recruitee\.com|jobs\.jobvite\.com|\.bamboohr\.com)",
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
_COVER_LETTER_SELECTORS = [
    "textarea[name*='cover' i]",
    "#cover_letter",
    "textarea[name*='letter' i]",
]
_SUBMIT_SELECTORS = ["#submit_app", "button[type='submit']", "input[type='submit']"]

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
        if href.split("?")[0].rstrip("/").endswith("/apply"):
            return href
    return None


def detect_form_mapping(session: BrowserSession) -> FormFieldMapping | None:
    """Build a mapping from what's visibly on the page, or None."""
    email = _first_visible(session, _EMAIL_SELECTORS)
    submit = _first_visible(session, _SUBMIT_SELECTORS)
    if email is None or submit is None:
        return None

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
        submit_selector=submit,
        success_selector=GENERIC_SUCCESS_SELECTOR,
    )


def prepare_application_page(session: BrowserSession, posting: JobPosting) -> str | None:
    """Navigate to the posting and onward to its application form.

    Returns an error reason, or None once a page that may hold the form
    is loaded. Never creates accounts or works around access walls —
    those are reported via the problem detectors afterwards.
    """
    try:
        session.goto(posting.url)
    except Exception as exc:
        return f"could not open {posting.url}: {exc}"

    if _first_visible(session, _BOT_PROTECTION_SELECTORS) is not None:
        return "the site is showing a bot-protection challenge — a human must apply here"

    if detect_form_mapping(session) is not None:
        return None  # the posting page itself is the form

    apply_url = find_apply_url(session)
    if apply_url is None:
        return "no application form or apply link found on the posting page"
    try:
        session.goto(apply_url)
    except Exception as exc:
        return f"could not open apply link {apply_url}: {exc}"
    return None
