"""Interview stage detection: a simple keyword heuristic."""

from __future__ import annotations

import re
from enum import StrEnum


class InterviewStage(StrEnum):
    PHONE_SCREEN = "phone_screen"
    TECHNICAL = "technical"
    ONSITE_FINAL = "onsite_final"
    GENERAL = "general"
    UNKNOWN = "unknown"


_STAGE_PATTERNS: list[tuple[InterviewStage, re.Pattern[str]]] = [
    (
        InterviewStage.ONSITE_FINAL,
        re.compile(r"\bonsite\b|\bfinal round\b|\bin[- ]person\b", re.I),
    ),
    (
        InterviewStage.TECHNICAL,
        re.compile(
            r"\btechnical (interview|screen|assessment)\b|\bcoding (interview|challenge)\b", re.I
        ),
    ),
    (
        InterviewStage.PHONE_SCREEN,
        re.compile(r"\bphone screen\b|\binitial call\b|\brecruiter call\b", re.I),
    ),
]


def detect_stage(text: str) -> InterviewStage:
    for stage, pattern in _STAGE_PATTERNS:
        if pattern.search(text):
            return stage
    if re.search(r"\binterview\b", text, re.I):
        return InterviewStage.GENERAL
    return InterviewStage.UNKNOWN
