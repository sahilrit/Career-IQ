"""Mock-interview practice: score a spoken/typed answer against the things that
actually make interview answers land — concreteness, metrics, and STAR shape.

Deterministic and zero-cost (the free tier). The API layer optionally enriches
the prose coaching with an LLM when the workspace has an AI key, but the
structured signals here are always computed the same way."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_METRIC_RE = re.compile(r"\d")
_RESULT_WORDS = (
    "result",
    "led to",
    "increased",
    "decreased",
    "reduced",
    "grew",
    "saved",
    "improved",
    "achieved",
    "drove",
    "impact",
    "so that",
    "as a result",
)
_SITUATION_WORDS = ("when", "because", "the problem", "challenge", "faced", "tasked", "goal was")
_FILLER_WORDS = ("um", "uh", "like", "you know", "basically", "kind of", "sort of")


@dataclass
class PracticeSignals:
    word_count: int
    has_metrics: bool
    mentions_result: bool
    sets_situation: bool
    uses_star: bool
    filler_count: int
    rating: int  # 1-5
    strengths: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)


def analyze_answer(answer: str) -> PracticeSignals:
    text = answer.strip()
    lower = text.lower()
    words = text.split()
    word_count = len(words)

    has_metrics = bool(_METRIC_RE.search(text))
    mentions_result = any(word in lower for word in _RESULT_WORDS)
    sets_situation = any(word in lower for word in _SITUATION_WORDS)
    uses_star = sets_situation and mentions_result
    filler_count = sum(lower.count(word) for word in _FILLER_WORDS)

    strengths: list[str] = []
    improvements: list[str] = []
    if has_metrics:
        strengths.append("You backed it with concrete numbers — interviewers remember those.")
    else:
        improvements.append("Add a specific metric (%, $, time saved) so the impact is measurable.")
    if mentions_result:
        strengths.append("You named the outcome, not just the activity.")
    else:
        improvements.append("End with the result — what changed because of what you did.")
    if not sets_situation:
        improvements.append(
            "Open by framing the situation and your specific task (the S and T of STAR)."
        )
    if word_count < 40:
        improvements.append("Too brief — expand to ~60-150 words so the story lands.")
    elif word_count > 300:
        improvements.append("Too long — tighten to the one story that best proves the point.")
    elif not strengths:
        strengths.append("Good length and focus.")
    if filler_count >= 4:
        improvements.append(f"Trim filler words (heard ~{filler_count}) — pause instead.")

    rating = 3
    if has_metrics:
        rating += 1
    if uses_star:
        rating += 1
    if word_count < 40:
        rating -= 1
    if filler_count >= 6:
        rating -= 1
    rating = max(1, min(5, rating))

    return PracticeSignals(
        word_count=word_count,
        has_metrics=has_metrics,
        mentions_result=mentions_result,
        sets_situation=sets_situation,
        uses_star=uses_star,
        filler_count=filler_count,
        rating=rating,
        strengths=strengths,
        improvements=improvements,
    )


def heuristic_feedback(signals: PracticeSignals) -> str:
    """Assemble prose coaching from the signals — the free-tier critique when no
    AI key is set."""
    parts = [f"Score: {signals.rating}/5."]
    if signals.strengths:
        parts.append("What worked: " + " ".join(signals.strengths))
    if signals.improvements:
        parts.append("To improve: " + " ".join(signals.improvements))
    return " ".join(parts)
