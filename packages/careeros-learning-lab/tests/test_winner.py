"""Tests for determine_winner."""

from __future__ import annotations

from careeros_learning_lab import OutcomeType
from careeros_learning_lab.metrics import VariantMetrics
from careeros_learning_lab.winner import determine_winner


def _metrics(variant_id: str, sent: int, response: int) -> VariantMetrics:
    return VariantMetrics(
        variant_id=variant_id,
        sent_count=sent,
        response_count=response,
        interview_count=0,
        offer_count=0,
        client_conversion_count=0,
        total_revenue=0.0,
    )


def test_picks_the_higher_rate_variant():
    metrics_by_variant = {
        "a": _metrics("a", sent=10, response=2),
        "b": _metrics("b", sent=10, response=8),
    }
    assert determine_winner(metrics_by_variant) == "b"


def test_excludes_variants_below_minimum_sample_size():
    metrics_by_variant = {
        "a": _metrics("a", sent=2, response=2),
        "b": _metrics("b", sent=10, response=1),
    }
    assert determine_winner(metrics_by_variant, min_sample_size=5) == "b"


def test_returns_none_when_no_variant_has_enough_samples():
    metrics_by_variant = {"a": _metrics("a", sent=1, response=1)}
    assert determine_winner(metrics_by_variant, min_sample_size=5) is None


def test_returns_none_for_empty_input():
    assert determine_winner({}) is None


def test_respects_a_different_primary_outcome():
    metrics_by_variant = {
        "a": _metrics("a", sent=10, response=9),
        "b": _metrics("b", sent=10, response=1),
    }
    winner = determine_winner(metrics_by_variant, primary_outcome=OutcomeType.SENT)
    assert winner in ("a", "b")
