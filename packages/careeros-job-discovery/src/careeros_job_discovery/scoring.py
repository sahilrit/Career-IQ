"""Heuristic match scoring between a job posting and a Career Brain.

Deliberately simple, explainable arithmetic — not an ML model. Phase 11
(Career Brain Engine) builds richer resume/experience intelligence on top
of this; this stays the cheap, fast first-pass score used to decide
whether a posting is even worth deeper analysis.
"""

from __future__ import annotations

import re

from careeros_career_brain import CareerBrain
from careeros_job_providers import JobPosting

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_PAREN_RE = re.compile(r"\(([^)]*)\)")

_SKILL_WEIGHT = 0.5
_TITLE_WEIGHT = 0.2
_SALARY_WEIGHT = 0.15
_LOCATION_WEIGHT = 0.15


def _tokenize(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _skill_phrases(skill_name: str) -> list[set[str]]:
    """A skill name as matchable token sets: the main phrase plus any
    parenthesized aliases, split on "/" — so "Meta Ads (Facebook/Instagram)"
    can match a posting that only says "facebook"."""
    aliases = [alias for group in _PAREN_RE.findall(skill_name) for alias in group.split("/")]
    main_phrase = _PAREN_RE.sub(" ", skill_name)
    token_sets = [_tokenize(phrase) for phrase in [main_phrase, *aliases]]
    return [tokens for tokens in token_sets if tokens]


def _skill_score(posting: JobPosting, brain: CareerBrain) -> float:
    if not brain.skills:
        return 0.0
    posting_terms = _tokenize(posting.title) | _tokenize(posting.description)
    for tag in posting.tags:
        posting_terms |= _tokenize(tag)
    matched = sum(
        1
        for skill in brain.skills
        if any(tokens <= posting_terms for tokens in _skill_phrases(skill.name))
    )
    return min(matched / len(brain.skills), 1.0)


def _title_score(posting: JobPosting, brain: CareerBrain) -> float:
    desired = brain.preferences.desired_titles
    if not desired:
        return 1.0  # no stated preference: don't penalize
    title_lower = posting.title.lower()
    return 1.0 if any(title.lower() in title_lower for title in desired) else 0.0


def _salary_score(posting: JobPosting, brain: CareerBrain) -> float:
    min_salary = brain.preferences.min_salary
    if min_salary is None:
        return 1.0
    midpoint = posting.salary.midpoint() if posting.salary else None
    if midpoint is None:
        return 0.5  # unknown: neither reward nor penalize fully
    return 1.0 if midpoint >= min_salary else 0.0


def _location_score(posting: JobPosting, brain: CareerBrain) -> float:
    preferences = brain.preferences
    if preferences.remote_only:
        return 1.0 if posting.remote else 0.0
    if not preferences.desired_locations:
        return 1.0
    if posting.remote:
        return 1.0
    if posting.location is None:
        return 0.5
    location_lower = posting.location.lower()
    return (
        1.0 if any(loc.lower() in location_lower for loc in preferences.desired_locations) else 0.0
    )


def score_posting(posting: JobPosting, brain: CareerBrain) -> float:
    """A 0.0-1.0 heuristic match score between ``posting`` and ``brain``."""
    return (
        _SKILL_WEIGHT * _skill_score(posting, brain)
        + _TITLE_WEIGHT * _title_score(posting, brain)
        + _SALARY_WEIGHT * _salary_score(posting, brain)
        + _LOCATION_WEIGHT * _location_score(posting, brain)
    )
