"""Mock-interview answer analysis (deterministic, free-tier)."""

from __future__ import annotations

from careeros_interview_intelligence import analyze_answer, heuristic_feedback


def test_strong_answer_scores_high():
    answer = (
        "When our checkout conversion stalled, I was tasked with fixing it. "
        "I ran A/B tests on the flow, which increased conversion by 22% and "
        "drove $180,000 in extra revenue that quarter as a result."
    )
    signals = analyze_answer(answer)
    assert signals.has_metrics is True
    assert signals.mentions_result is True
    assert signals.uses_star is True
    assert signals.rating >= 4
    assert "Score:" in heuristic_feedback(signals)


def test_weak_answer_gets_actionable_improvements():
    signals = analyze_answer("I worked on ads and did a good job.")
    assert signals.has_metrics is False
    assert signals.rating <= 3
    # tells the user exactly what to add
    assert any("metric" in tip.lower() for tip in signals.improvements)
    assert any("result" in tip.lower() for tip in signals.improvements)
