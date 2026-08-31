"""What a control on an application form actually IS.

Two questions, both previously answered by "the first selector that matched",
and both answered wrongly often enough to break real applications:

1. **Which button submits the application?** On a live Ashby form there are
   forty ``button[type=submit]`` elements. Every "Upload file" control is one.
   Picking by selector picked "Upload file", so the autopilot's submit click
   would have opened a file dialog while believing it had applied. A selector
   cannot answer this question; only the control's *meaning* can.

2. **What is this field for?** "First Name", "Given Name", "Legal First Name"
   and "Forename" are the same field. So are "Phone", "Mobile", "Telephone"
   and "Contact Number". A hardcoded ``input[name*='first']`` matches the
   first and misses the rest, and matches "First Language" by accident.

So both are decided by *classification over signals*, not by selector
matching. Everything here is a pure function over a descriptor dict, which
means every real-world form that ever fooled us becomes a fixture and a test
rather than a bug that can come back.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from functools import lru_cache


class ControlKind(StrEnum):
    """What clicking a control does. The distinctions are the ones that matter
    for safety: only ``SUBMIT_APPLICATION`` may ever be clicked automatically,
    and ``UPLOAD`` must never be."""

    #: Sends the application. The only control the runner may finally click.
    SUBMIT_APPLICATION = "submit_application"
    #: Opens a file dialog. Clicking this believing it submits is the exact
    #: bug this module exists to prevent.
    UPLOAD = "upload"
    #: Advances a multi-step form without sending anything.
    CONTINUE = "continue"
    #: Same, when the form calls it "Next".
    NEXT = "next"
    #: Saves a draft.
    SAVE = "save"
    #: Goes to a review/preview step.
    REVIEW = "review"
    #: Cancel, back, clear — destructive or backwards. Never clicked.
    CANCEL = "cancel"
    #: An answer button (Yes/No), a menu toggle, anything else.
    OTHER = "other"


#: Phrases that identify a control, most specific first. Matched against the
#: accessible name (which falls back to visible text), lowercased and squashed.
#: Order is load-bearing: "save and continue" is a CONTINUE, not a SAVE, and
#: "submit" inside "submit resume" is an UPLOAD, not a submission.
_CONTROL_PHRASES: tuple[tuple[str, ControlKind], ...] = (
    # Upload first — several upload controls contain the word "submit".
    ("upload", ControlKind.UPLOAD),
    ("attach", ControlKind.UPLOAD),
    ("choose file", ControlKind.UPLOAD),
    ("select file", ControlKind.UPLOAD),
    ("browse", ControlKind.UPLOAD),
    ("add file", ControlKind.UPLOAD),
    ("drop file", ControlKind.UPLOAD),
    ("submit resume", ControlKind.UPLOAD),
    ("submit cv", ControlKind.UPLOAD),
    # Backwards / destructive.
    ("cancel", ControlKind.CANCEL),
    ("go back", ControlKind.CANCEL),
    ("previous", ControlKind.CANCEL),
    ("clear", ControlKind.CANCEL),
    ("discard", ControlKind.CANCEL),
    ("delete", ControlKind.CANCEL),
    ("remove", ControlKind.CANCEL),
    # Progress within a form. Checked before SAVE so "save and continue" is
    # correctly a step forward rather than a draft save.
    ("save and continue", ControlKind.CONTINUE),
    ("save & continue", ControlKind.CONTINUE),
    ("continue", ControlKind.CONTINUE),
    ("next step", ControlKind.NEXT),
    ("next", ControlKind.NEXT),
    ("proceed", ControlKind.CONTINUE),
    ("save draft", ControlKind.SAVE),
    ("save for later", ControlKind.SAVE),
    ("save", ControlKind.SAVE),
    ("review", ControlKind.REVIEW),
    ("preview", ControlKind.REVIEW),
    # Actual submission. Every one of these is an explicit, unambiguous
    # "this sends it" phrase — a bare "submit" is handled separately below,
    # because on its own it is genuinely ambiguous.
    ("submit application", ControlKind.SUBMIT_APPLICATION),
    ("submit my application", ControlKind.SUBMIT_APPLICATION),
    ("send application", ControlKind.SUBMIT_APPLICATION),
    ("submit your application", ControlKind.SUBMIT_APPLICATION),
    ("apply for this job", ControlKind.SUBMIT_APPLICATION),
    ("apply now", ControlKind.SUBMIT_APPLICATION),
    ("send my application", ControlKind.SUBMIT_APPLICATION),
    ("submit profile", ControlKind.SUBMIT_APPLICATION),
)

#: Standalone words that mean submission only when they are the WHOLE label.
#: "Submit" alone submits; "Submit resume" uploads; "Resubmit search" does
#: neither, and substring matching cannot tell them apart.
_EXACT_SUBMIT_LABELS = frozenset({"submit", "apply", "send", "finish", "complete application"})

_WHITESPACE_RE = re.compile(r"\s+")
#: Trailing decoration on a label: the required-marker asterisk, the colon
#: after "Email:", a full stop. Stripped so "Email:" and "Email" are one label.
_LABEL_EDGE_RE = re.compile(r"^[\s.:*]+|[\s.:*]+$")


def normalize_label(text: str) -> str:
    """Lowercased, whitespace-squashed, punctuation-trimmed."""
    squashed = _WHITESPACE_RE.sub(" ", (text or "").strip().lower())
    return _LABEL_EDGE_RE.sub("", squashed)


def classify_control(descriptor: dict) -> ControlKind:
    """What the control described by ``descriptor`` does.

    ``descriptor`` is one row from ``BrowserSession.detect_buttons``.
    """
    name = normalize_label(
        str(descriptor.get("accessible_name") or "") or str(descriptor.get("text") or "")
    )

    # The label decides first. An explicitly labelled control means what it
    # says, and letting a DOM proximity signal override that got "Apply for
    # this job" classified as an upload button on a one-column form where the
    # button and the CV field simply share a parent.
    if name in _EXACT_SUBMIT_LABELS:
        return ControlKind.SUBMIT_APPLICATION
    for phrase, kind in _CONTROL_PHRASES:
        if phrase in name:
            return kind

    # Only for controls the label could not identify: one sitting inside a
    # file-upload widget is an upload control. This is what catches the
    # unlabelled ones ("Add", an icon-only button) that a phrase list cannot.
    if descriptor.get("near_file_input"):
        return ControlKind.UPLOAD

    return ControlKind.OTHER


@dataclass(frozen=True)
class SubmitCandidate:
    selector: str
    label: str
    kind: ControlKind
    disabled: bool
    #: Why this one was chosen (or rejected) — kept so a wrong choice can be
    #: explained rather than merely observed.
    reason: str = ""


def find_submit_control(descriptors: list[dict]) -> SubmitCandidate | None:
    """The control that sends the application, or None if there isn't one.

    Returns None rather than a best guess. "No submit button found" is a
    correct, recoverable outcome — a human finishes the form. "We clicked
    something that was not the submit button" is not recoverable, because by
    then a file dialog is open, or a draft is saved, or a partial application
    has been sent.
    """
    classified = [
        SubmitCandidate(
            selector=str(row.get("selector") or ""),
            label=normalize_label(
                str(row.get("accessible_name") or "") or str(row.get("text") or "")
            ),
            kind=classify_control(row),
            disabled=bool(row.get("disabled")),
        )
        for row in descriptors
        if row.get("selector")
    ]
    submitters = [c for c in classified if c.kind is ControlKind.SUBMIT_APPLICATION]
    if not submitters:
        return None

    enabled = [c for c in submitters if not c.disabled]
    if not enabled:
        # A disabled submit button is real and is worth reporting: it usually
        # means a required field is still empty, which is actionable.
        chosen = submitters[-1]
        return SubmitCandidate(
            selector=chosen.selector,
            label=chosen.label,
            kind=chosen.kind,
            disabled=True,
            reason="the submit button is disabled — the form is not complete yet",
        )
    # Last in document order: forms put the real submit at the bottom, and a
    # "Submit application" that appears early is usually a header CTA that
    # scrolls rather than submits.
    chosen = enabled[-1]
    return SubmitCandidate(
        selector=chosen.selector,
        label=chosen.label,
        kind=chosen.kind,
        disabled=False,
        reason=f"matched submit semantics on {chosen.label!r}",
    )


# ── field purpose ──────────────────────────────────────────────────────────


class FieldPurpose(StrEnum):
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    FULL_NAME = "full_name"
    EMAIL = "email"
    PHONE = "phone"
    RESUME = "resume"
    COVER_LETTER = "cover_letter"
    LINKEDIN = "linkedin"
    GITHUB = "github"
    PORTFOLIO = "portfolio"
    LOCATION = "location"
    CURRENT_EMPLOYER = "current_employer"
    CURRENT_TITLE = "current_title"
    #: A real question that is not one of the standard identity fields. These
    #: go to the answerer, not to the profile mapper.
    QUESTION = "question"


@dataclass
class PurposeRule:
    purpose: FieldPurpose
    #: Any of these in the combined label text is a match.
    phrases: tuple[str, ...] = ()
    #: Any of these anywhere disqualifies the match outright. This is what
    #: keeps "First Language" out of FIRST_NAME and "How did you hear about
    #: this role?" out of LOCATION.
    excludes: tuple[str, ...] = ()
    #: HTML autocomplete tokens that settle it on their own — the one signal
    #: a site sets deliberately and correctly.
    autocomplete: tuple[str, ...] = ()
    #: input types that settle it on their own.
    input_types: tuple[str, ...] = ()


#: Ordered most specific first. "last name" must beat "name"; "linkedin url"
#: must beat "url".
PURPOSE_RULES: tuple[PurposeRule, ...] = (
    PurposeRule(
        FieldPurpose.EMAIL,
        # "e mail" as well as "e-mail": signal text normalises hyphens to
        # spaces, so the hyphenated form alone would never match.
        phrases=("email", "e-mail", "e mail", "email address"),
        autocomplete=("email",),
        input_types=("email",),
    ),
    PurposeRule(
        FieldPurpose.LINKEDIN,
        # "linked in" covers the attribute form ("linkedInUrl" split on case).
        phrases=("linkedin", "linked in"),
    ),
    PurposeRule(FieldPurpose.GITHUB, phrases=("github", "git hub")),
    PurposeRule(
        FieldPurpose.PORTFOLIO,
        phrases=("portfolio", "personal website", "personal site", "website", "web site"),
        excludes=("company website", "employer website"),
    ),
    PurposeRule(
        FieldPurpose.PHONE,
        phrases=(
            "phone",
            "mobile",
            "telephone",
            "tel.",
            "contact number",
            "cell",
            "whatsapp",
        ),
        autocomplete=("tel",),
        input_types=("tel",),
    ),
    PurposeRule(
        FieldPurpose.LAST_NAME,
        phrases=(
            "last name",
            "lastname",
            "surname",
            "family name",
            "legal last name",
            "second name",
        ),
        autocomplete=("family-name",),
    ),
    PurposeRule(
        FieldPurpose.FIRST_NAME,
        phrases=(
            "first name",
            "firstname",
            "given name",
            "legal first name",
            "forename",
            "preferred first name",
        ),
        # "First Language" and "First day available" are not names.
        excludes=("language", "day", "date", "job", "role", "company"),
        autocomplete=("given-name",),
    ),
    PurposeRule(
        FieldPurpose.CURRENT_EMPLOYER,
        phrases=(
            "current employer",
            "current company",
            "present employer",
            "present company",
            "most recent employer",
            "most recent company",
            "employer name",
            "company name",
        ),
        excludes=("why", "describe"),
        autocomplete=("organization",),
    ),
    PurposeRule(
        FieldPurpose.CURRENT_TITLE,
        phrases=(
            "current title",
            "current job title",
            "current role",
            "present title",
            "most recent title",
            "job title",
            "your title",
        ),
        autocomplete=("organization-title",),
    ),
    PurposeRule(
        FieldPurpose.FULL_NAME,
        phrases=("full name", "your name", "legal name", "name"),
        # A rule this broad needs a wide exclusion list, or it swallows every
        # field whose label merely contains the word "name".
        excludes=(
            "first",
            "last",
            "sur",
            "family",
            "given",
            "middle",
            "user",
            "company",
            "employer",
            "school",
            "university",
            "file",
            "reference",
            "pronoun",
            "preferred",
        ),
        autocomplete=("name",),
    ),
    PurposeRule(
        FieldPurpose.RESUME,
        phrases=("resume", "résumé", "cv", "curriculum vitae"),
        excludes=("cover",),
    ),
    PurposeRule(
        FieldPurpose.COVER_LETTER,
        phrases=("cover letter", "covering letter", "motivation letter"),
    ),
    PurposeRule(
        FieldPurpose.LOCATION,
        phrases=("location", "city", "where are you based", "town", "country of residence"),
        excludes=("relocate", "willing", "preferred location", "citizenship"),
    ),
)


def _signal_text(descriptor: dict) -> str:
    """Every label signal for one field, combined.

    Combined rather than "the first non-empty one", because sites disagree
    about which signal is authoritative, and a field labelled only by its
    ``name`` attribute is common enough that ignoring it loses real fields.
    ``heading`` is deliberately NOT included — it is section context ("Contact
    details"), and treating it as a label makes every field in a section look
    like the section.
    """
    human = [
        descriptor.get("aria_label") or "",
        descriptor.get("label") or "",
        descriptor.get("placeholder") or "",
    ]
    machine = [descriptor.get("name") or "", descriptor.get("id_attr") or ""]
    # Only ATTRIBUTE values get camelCase/snake/kebab split, so "firstName"
    # and "first_name" both read as "first name". Human labels are left
    # alone: splitting them turns "LinkedIn" into "Linked In", which then
    # matches nothing.
    machine_text = re.sub(r"([a-z])([A-Z])", r"\1 \2", " ".join(str(p) for p in machine if p))
    combined = " ".join([*(str(p) for p in human if p), machine_text])
    # Underscores and hyphens are separators everywhere, human or machine.
    return normalize_label(combined.replace("_", " ").replace("-", " "))


@lru_cache(maxsize=512)
def _phrase_re(phrase: str) -> re.Pattern[str]:
    """A phrase matcher anchored on WORD boundaries.

    Plain substring matching mapped "Race / Ethnicity" to LOCATION, because
    "city" is inside "ethni-CITY" — the identical trap the rules-based answerer
    already documents. Anchoring every phrase (not just the one that bit)
    protects the rules that have not been tripped over yet.
    """
    return re.compile(rf"\b{re.escape(phrase)}\b")


def _mentions(text: str, phrases: tuple[str, ...]) -> bool:
    return any(_phrase_re(phrase).search(text) for phrase in phrases)


def classify_field(descriptor: dict) -> FieldPurpose:
    """What a form field is for, from every signal the page offers.

    ``descriptor`` is one row from ``BrowserSession.detect_fields``.
    """
    text = _signal_text(descriptor)
    autocomplete = normalize_label(str(descriptor.get("autocomplete") or ""))
    input_type = normalize_label(str(descriptor.get("type") or ""))

    # A file input can only be a résumé or a cover letter; deciding that here
    # stops a résumé being uploaded into the cover-letter slot on forms with
    # both, which is a real thing that happened.
    if input_type == "file":
        if _mentions(text, ("cover", "letter", "motivation")):
            return FieldPurpose.COVER_LETTER
        return FieldPurpose.RESUME

    for rule in PURPOSE_RULES:
        if rule.autocomplete and autocomplete in rule.autocomplete:
            return rule.purpose
        if rule.input_types and input_type in rule.input_types:
            return rule.purpose
        if _mentions(text, rule.excludes):
            continue
        if _mentions(text, rule.phrases):
            return rule.purpose

    return FieldPurpose.QUESTION


@dataclass
class MappedField:
    selector: str
    purpose: FieldPurpose
    label: str
    kind: str = "text"
    required: bool = False
    options: list[str] = field(default_factory=list)
    #: For a ``choice`` field: option label → the selector that picks it.
    #: Choosing means clicking the right control, so the mapping must survive
    #: all the way to the fill.
    option_selectors: dict[str, str] = field(default_factory=dict)


#: Control types that are CHOSEN by clicking one of several controls, rather
#: than written to. Text-filling one raises.
_CHOICE_TYPES = frozenset({"radio", "checkbox"})


def map_fields(descriptors: list[dict]) -> list[MappedField]:
    """Every detected field, classified. Order preserved.

    Radio and checkbox controls are COLLAPSED by group: eleven EEO radio
    buttons are one question with eleven options, not eleven questions. Each
    one's own label names an option ("Decline to self-identify"), so treating
    them separately produced eleven unanswerable required questions — and then
    tried to text-fill a radio, which raises.

    Disabled and readonly fields are dropped: writing to them cannot work, and
    including them turns a fill that was never possible into a reported
    failure the user cannot act on.
    """
    mapped: list[MappedField] = []
    #: group key -> index into ``mapped``, so later options join the first.
    groups: dict[str, int] = {}

    for row in descriptors:
        selector = str(row.get("selector") or "")
        if not selector or row.get("disabled") or row.get("readonly"):
            continue
        tag = str(row.get("tag") or "input")
        input_type = str(row.get("type") or "text").lower()
        label = (
            str(row.get("label") or "")
            or str(row.get("aria_label") or "")
            or str(row.get("placeholder") or "")
        )

        if input_type in _CHOICE_TYPES:
            option = normalize_label(str(row.get("option_label") or "")) or normalize_label(label)
            key = str(row.get("group_name") or "") or normalize_label(label)
            existing = groups.get(key)
            if existing is not None:
                target = mapped[existing]
                if option and option not in target.options:
                    target.options.append(option)
                    target.option_selectors[option] = selector
                # A group is required if ANY of its controls says so.
                target.required = target.required or bool(row.get("required"))
                continue
            groups[key] = len(mapped)
            mapped.append(
                MappedField(
                    selector=selector,
                    purpose=classify_field(row),
                    label=normalize_label(label),
                    kind="choice",
                    required=bool(row.get("required")),
                    options=[option] if option else [],
                    option_selectors={option: selector} if option else {},
                )
            )
            continue

        kind = "select" if tag == "select" else ("file" if input_type == "file" else "text")
        mapped.append(
            MappedField(
                selector=selector,
                purpose=classify_field(row),
                label=normalize_label(label),
                kind=kind,
                required=bool(row.get("required")),
                options=[str(o) for o in (row.get("options") or [])],
            )
        )
    return mapped
