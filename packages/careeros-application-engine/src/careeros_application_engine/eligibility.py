"""Spot a job that *explicitly* rules the candidate out, so the autopilot can
skip it instead of preparing a form they can't qualify for.

This is deliberately conservative. It only fires on unambiguous, hard
requirements the candidate provably cannot meet given their *stored* answers
(US work authorization, visa sponsorship, being US-based, a stated minimum
years of experience) — never on soft preferences ("US time zone preferred")
or on a guess. When in doubt it stays silent and the application proceeds,
because wrongly discarding a job the person could have gotten is worse than
letting a human glance at a long shot.

Nothing here is hardcoded to one user: every check is gated on what that
Career Brain actually stored. A candidate who *is* US-authorized triggers none
of the US-authorization checks.
"""

from __future__ import annotations

import re
from datetime import date

from careeros_career_brain import CareerBrain

# "we do not / cannot / are unable to sponsor", "no visa sponsorship",
# "sponsorship is not available", "without sponsorship".
_SPONSORSHIP_RE = re.compile(
    r"(do(es)?\s+not\s+(offer\s+|provide\s+)?sponsor"
    r"|cannot\s+sponsor|can'?t\s+sponsor|will\s+not\s+sponsor"
    r"|not\s+(able|willing)\s+to\s+(provide|offer|sponsor)"
    r"|unable\s+to\s+sponsor"
    r"|no\s+(visa\s+)?sponsorship"
    r"|without\s+(visa\s+)?sponsorship"
    r"|sponsorship\s+(is\s+)?not\s+(available|offered|provided)"
    r"|not\s+(provide|offer)\s+(visa\s+)?sponsorship)",
    re.IGNORECASE,
)

# Must be authorized / eligible to work in the US, or be a US citizen, or hold
# a clearance (which requires citizenship).
_US_WORK_AUTH_RE = re.compile(
    r"(must\s+be\s+(legally\s+)?(authori[sz]ed|eligible)\s+to\s+work\s+in\s+the\s+"
    r"(us|u\.s\.?|united\s+states)"
    r"|(us|u\.s\.?|united\s+states)\s+work\s+authori[sz]ation\s+(is\s+)?required"
    r"|require[sd]?\s+(us|u\.s\.?|united\s+states)\s+work\s+authori[sz]ation"
    r"|must\s+(have|hold)\s+(a\s+)?(us|u\.s\.?|united\s+states)\s+work\s+authori[sz]ation"
    r"|must\s+be\s+a\s+(us|u\.s\.?|united\s+states)\s+citizen"
    r"|(us|u\.s\.?|united\s+states)\s+citizen(ship)?\s+(is\s+)?(required|only)"
    r"|(active\s+)?security\s+clearance\s+(is\s+)?required"
    r"|requires?\s+(an\s+)?active\s+security\s+clearance)",
    re.IGNORECASE,
)

# The job is restricted to people physically in the US.
_US_ONLY_LOCATION_RE = re.compile(
    r"((us|u\.s\.?|united\s+states)[-\s]based\s+(candidates?|applicants?|only)"
    r"|must\s+(be\s+(located|based)\s+in|reside\s+in)\s+the\s+(us|u\.s\.?|united\s+states)"
    r"|(located|based)\s+in\s+the\s+(us|u\.s\.?|united\s+states)\s+only"
    r"|open\s+to\s+(us|u\.s\.?|united\s+states)\s+(residents?|candidates?)\s+only)",
    re.IGNORECASE,
)


# A stated MINIMUM years-of-experience requirement — anchored to "years ...
# experience" phrasing specifically, so an unrelated mention of a number of
# years ("founded 10 years ago") is never mistaken for one. A range ("5-10
# years") captures the lower bound, which is the actual minimum a candidate
# needs to meet.
_EXPERIENCE_REQUIREMENT_RE = re.compile(
    r"(?:at\s+least\s+|minimum\s+(?:of\s+)?|requires?\s+)?"
    r"(\d{1,2})\+?\s*(?:-\s*\d{1,2}\s*)?"
    r"years?\s+(?:of\s+)?(?:relevant\s+|professional\s+|work\s+)?experience",
    re.IGNORECASE,
)


def _location_is_us(brain: CareerBrain) -> bool:
    location = (brain.identity.location or "").lower()
    return any(token in location for token in ("united states", "u.s.", " us", "usa"))


def _total_years_experience(brain: CareerBrain) -> float | None:
    """The candidate's career span in years — earliest start to latest
    end-or-now — or None with nothing stored.

    Deliberately the generous reading (counts any gaps between roles as
    experience too): this gate only ever disqualifies, so overestimating
    the candidate's experience is the safe direction to round.
    """
    if not brain.experiences:
        return None
    earliest = min(experience.start_date for experience in brain.experiences)
    latest = max(experience.end_date or date.today() for experience in brain.experiences)
    return (latest - earliest).days / 365.25


def _insufficient_experience(brain: CareerBrain, combined: str) -> str | None:
    match = _EXPERIENCE_REQUIREMENT_RE.search(combined)
    if not match:
        return None
    required_years = int(match.group(1))
    actual_years = _total_years_experience(brain)
    if actual_years is None or actual_years >= required_years:
        return None
    return f"role wants {required_years}+ years of experience; you have about {actual_years:.0f}"


def disqualifying_requirement(brain: CareerBrain, *texts: str | None) -> str | None:
    """A short reason this candidate is *explicitly* ineligible for the job
    described by ``texts`` (title, description, and/or the loaded form's text),
    or ``None`` if nothing rules them out.

    Only checks the candidate provably fails are run, keyed on the Career
    Brain's stored answers; unset answers activate no checks.
    """
    combined = " ".join(text for text in texts if text)
    if not combined.strip():
        return None
    # Collapse whitespace so "work\n in  the US" still matches.
    combined = re.sub(r"\s+", " ", combined)

    preferences = brain.preferences
    if preferences.needs_visa_sponsorship is True and _SPONSORSHIP_RE.search(combined):
        return "role does not offer the visa sponsorship you need"
    if preferences.us_work_authorized is False and _US_WORK_AUTH_RE.search(combined):
        return "role requires US work authorization / citizenship you don't have"
    location_matters = preferences.us_work_authorized is False or (
        preferences.remote_only and not _location_is_us(brain)
    )
    if location_matters and _US_ONLY_LOCATION_RE.search(combined):
        return "role is restricted to US-based candidates"
    return _insufficient_experience(brain, combined)
